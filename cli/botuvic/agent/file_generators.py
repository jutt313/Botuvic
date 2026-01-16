"""
File Generators for BOTUVIC.
Generates all project documentation and configuration files.
"""

import os
import json
import secrets
from typing import Dict, Any, List
from datetime import datetime


class FileGenerator:
    """Generates project files based on collected data."""

    def __init__(self, project_dir: str, storage, llm_manager=None):
        self.project_dir = project_dir
        self.storage = storage
        self.llm_manager = llm_manager

    def _generate_section_with_llm(self, section_name: str, prompt: str, context: Dict) -> str:
        """Generate detailed content for a section using LLM."""
        if not self.llm_manager:
            return f"<!-- {section_name}: LLM not available, add details manually -->\n"

        try:
            # Build context string
            context_str = ""
            if context.get("project_name"):
                context_str += f"Project: {context.get('project_name')}\n"
            if context.get("idea"):
                context_str += f"Idea: {context.get('idea')}\n"
            if context.get("features"):
                context_str += f"Features: {', '.join(context.get('features', []))}\n"
            if context.get("tech_stack"):
                context_str += f"Tech Stack: {json.dumps(context.get('tech_stack'), indent=2)}\n"
            if context.get("tables"):
                context_str += f"Database Tables: {', '.join(context.get('tables', []))}\n"

            full_prompt = f"""You are generating documentation for a software project.

PROJECT CONTEXT:
{context_str}

TASK: {prompt}

RULES:
- Be specific to THIS project (use actual names, features, tables)
- Include concrete details, not generic placeholders
- Use markdown formatting
- Be comprehensive but concise
- No fluff, just useful information

Generate the content now:"""

            response = self.llm_manager.chat([{"role": "user", "content": full_prompt}])
            # Extract content from response dict
            if isinstance(response, dict):
                content = response.get("content", "")
            else:
                content = str(response) if response else ""
            return content.strip() if content else ""
        except Exception as e:
            return f"<!-- Error generating {section_name}: {e} -->\n"

    def generate_all(self) -> Dict[str, bool]:
        """Generate all project files."""
        results = {}

        # Load all data (try multiple keys for compatibility)
        project = self.storage.load("project_info") or self.storage.load("project") or {}
        profile = self.storage.load("profile") or self.storage.load("user_profile") or {}
        db_schema = self.storage.load("database_schema") or self.storage.load("db_schema") or {}
        backend_arch = self.storage.load("backend_architecture") or self.storage.load("backend_design") or {}
        frontend_design = self.storage.load("frontend_design") or {}
        build_strategy = self.storage.load("build_strategy") or {}
        roadmap = self.storage.load("roadmap") or self.storage.load("development_roadmap") or {}
        tech_stack = self.storage.load("tech_stack") or project.get("tech_stack", {})
        external_tools = self.storage.load("external_tools") or project.get("external_tools", [])

        # Merge tech_stack and external_tools into project if not already there
        if tech_stack and "tech_stack" not in project:
            project["tech_stack"] = tech_stack
        if external_tools and "external_tools" not in project:
            project["external_tools"] = external_tools

        # CORE DOCUMENTATION FILES (Foundation)
        results["prd.md"] = self._generate_prd_md(project, profile)
        results["database.md"] = self._generate_database_md(project, db_schema)
        results["backend.md"] = self._generate_backend_md_v2(project, backend_arch, db_schema)
        results["frontend.md"] = self._generate_frontend_md(project, frontend_design, backend_arch)
        
        # SUMMARY FILES (Generated from core docs)
        results["plan.md"] = self._generate_plan_md(project, db_schema, backend_arch, frontend_design, roadmap)
        results["task.md"] = self._generate_task_md(project, roadmap)
        
        # TEST & TRACKING FILES
        results["test-plan.md"] = self._generate_test_plan_md(project, roadmap)
        results["progress-tracker.md"] = self._generate_progress_tracker_md(project)
        
        # CONFIG FILES
        results[".env.example"] = self._generate_env_example(project)
        results[".gitignore"] = self._generate_gitignore(project)
        results["README.md"] = self._generate_readme(project)

        # BUILDER-SPECIFIC FILES
        builder = build_strategy.get("builder", "")
        ai_tool_name = build_strategy.get("ai_tool_name", "")
        team_or_solo = profile.get("team_or_solo", "solo")
        team_members = build_strategy.get("team_members", [])

        # Generate AI/Developer instruction file
        if ai_tool_name:
            # Generic AI instruction file (works with any AI tool)
            results[f"{ai_tool_name.lower()}.md"] = self._generate_ai_instructions(
                project, db_schema, backend_arch, frontend_design, roadmap, ai_tool_name
            )
        elif builder == "self" or builder == "manual":
            results["development-guide.md"] = self._generate_dev_guide(project, db_schema, backend_arch, frontend_design, roadmap)

        # Generate team-specific files if working with a team
        if team_or_solo == "team" and team_members:
            # Create team folder
            team_dir = os.path.join(self.project_dir, "team")
            os.makedirs(team_dir, exist_ok=True)
            
            for member in team_members:
                # Handle both dict and string formats
                if isinstance(member, dict):
                member_name = member.get("name", "").lower().replace(" ", "-")
                member_role = member.get("role", "developer")
                else:
                    # If member is a string, use it as name
                    member_name = str(member).lower().replace(" ", "-")
                    member_role = "developer"
                    member = {"name": str(member), "role": "developer"}

                file_name = f"team/{member_name}-{member_role}.md"
                results[file_name] = self._generate_team_member_file(
                    project, member, db_schema, backend_arch, frontend_design, roadmap
                )

        return results

    def _get_project_name(self, project: Dict) -> str:
        """Extract project name from project data with multiple fallbacks."""
        # Try direct name fields
        name = project.get("name") or project.get("project_name") or project.get("app_name")
        if name and name != "Project":
            return name

        # Try to extract from idea (first word if it looks like a name)
        idea = project.get("idea") or project.get("core_idea") or ""
        if idea:
            # If idea starts with a capitalized word followed by dash or colon, use that
            import re
            match = re.match(r'^([A-Z][A-Za-z0-9]+)[\s\-—:]', idea)
            if match:
                return match.group(1)

        # Try loading from storage directly
        stored_project = self.storage.load("project") or {}
        if stored_project.get("name"):
            return stored_project.get("name")

        return "Project"

    def _generate_plan_md(self, project: Dict, db_schema: Dict, backend_arch: Dict, frontend_design: Dict, roadmap: Dict) -> bool:
        """Generate plan.md file - Summary with LLM-generated detailed sections."""
        # Get project info with fallbacks for different key names
        project_name = self._get_project_name(project)
        idea = project.get("idea", project.get("core_idea", project.get("description", "")))
        target_users = project.get("target_users", project.get("users", ""))
        features = project.get("features", project.get("main_features", []))

        # Get tech_stack from project or load separately
        tech_stack = project.get("tech_stack", {})
        if not tech_stack:
            tech_stack = self.storage.load("tech_stack") or {}

        # Build context for LLM
        tables_list = []
        if db_schema:
            tables = db_schema.get("tables", [])
            if isinstance(tables, list):
                for t in tables:
                    if isinstance(t, dict):
                        tables_list.append(t.get("name", ""))
                    else:
                        tables_list.append(str(t))

        context = {
            "project_name": project_name,
            "idea": idea,
            "features": features if isinstance(features, list) else [features],
            "tech_stack": tech_stack,
            "tables": tables_list,
            "target_users": target_users
        }

        content = f"""# {project_name} - Development Plan

Generated by BOTUVIC on {datetime.now().strftime("%Y-%m-%d")}

---

## 📚 Documentation Guide

| Document | Purpose |
|----------|---------|
| `prd.md` | Complete product requirements and user stories |
| `database.md` | Full database schema, relationships, and operations |
| `backend.md` | API documentation, endpoints, and architecture |
| `frontend.md` | UI/UX specifications, components, and flows |
| `task.md` | Detailed task breakdown with checkboxes |
| `test-plan.md` | Comprehensive testing strategy |

---

## 🎯 Executive Summary

"""
        # LLM generates executive summary
        exec_summary = self._generate_section_with_llm(
            "Executive Summary",
            f"Write a 3-4 paragraph executive summary for {project_name}. Include: what the app does, key value proposition, target market, and competitive advantage. Be specific and compelling.",
            context
        )
        content += exec_summary + "\n\n"

        content += """---

## 👥 Target Users & Market

"""
        # LLM generates detailed user analysis
        user_analysis = self._generate_section_with_llm(
            "Target Users",
            f"Create detailed user personas for {project_name}. Include: 2-3 specific user personas with demographics, pain points, goals, and how this app helps them. Use bullet points and be specific.",
            context
        )
        content += user_analysis + "\n\n"

        content += """---

## ✨ Core Features (Detailed)

"""
        # List features first, then get detailed breakdown
        for i, feature in enumerate(features, 1):
            content += f"{i}. **{feature}**\n"
        content += "\n"

        # LLM generates feature details
        feature_details = self._generate_section_with_llm(
            "Feature Details",
            f"For each feature of {project_name}, provide: user story (As a... I want... So that...), acceptance criteria (3-5 bullet points), and priority (Must-have/Should-have/Nice-to-have). Features: {', '.join(features)}",
            context
        )
        content += feature_details + "\n\n"

        content += """---

## 🛠 Tech Stack & Architecture

"""
        if tech_stack:
            content += "### Selected Technologies\n\n"
            for key, value in tech_stack.items():
                if isinstance(value, dict):
                    name = value.get("name", "")
                    reason = value.get("reason", "")
                    content += f"- **{key.title()}**: {name}\n"
                    if reason:
                        content += f"  - *Reason*: {reason}\n"
                else:
                    content += f"- **{key.title()}**: {value}\n"
            content += "\n"

        # LLM generates architecture overview
        arch_overview = self._generate_section_with_llm(
            "Architecture",
            f"Describe the high-level architecture for {project_name}. Include: system diagram description (frontend → API → database), data flow, key integrations, and scalability considerations. Tech stack: {json.dumps(tech_stack)}",
            context
        )
        content += "### Architecture Overview\n\n" + arch_overview + "\n\n"

        content += """---

## 🗄 Database Design

"""
        if db_schema:
            tables = db_schema.get("tables", {})
            if isinstance(tables, list):
                for table in tables:
                    if isinstance(table, dict):
                        table_name = table.get("name", "unknown")
                content += f"### {table_name}\n\n"
                        fields = table.get("fields", [])
                        content += "| Column | Type | Constraints |\n|--------|------|-------------|\n"
                for field in fields:
                            if isinstance(field, dict):
                                content += f"| {field.get('name', '')} | {field.get('type', '')} | {field.get('constraints', '')} |\n"
                            else:
                                content += f"| {field} | - | - |\n"
                content += "\n"

        # LLM generates relationship explanations
        db_relationships = self._generate_section_with_llm(
            "Database Relationships",
            f"Explain the database relationships for {project_name} with tables: {', '.join(tables_list)}. Describe: one-to-many, many-to-many relationships, foreign keys, and data integrity rules.",
            context
        )
        content += "### Relationships & Data Flow\n\n" + db_relationships + "\n\n"

        content += """---

## 📅 Development Roadmap

"""
        # LLM generates detailed week-by-week plan
        dev_roadmap = self._generate_section_with_llm(
            "Development Roadmap",
            f"Create a detailed week-by-week development roadmap for {project_name}. Include 4-6 phases: Setup, Backend Development, Frontend Development, Integration, Testing, Deployment. For each phase: duration, specific tasks, deliverables, and success criteria.",
            context
        )
        content += dev_roadmap + "\n\n"

        content += """---

## ⚠️ Risks & Mitigation

"""
        # LLM generates risk analysis
        risk_analysis = self._generate_section_with_llm(
            "Risks",
            f"Identify 5-7 potential risks for {project_name} development. For each: risk description, probability (Low/Medium/High), impact (Low/Medium/High), and mitigation strategy. Include technical, resource, and timeline risks.",
            context
        )
        content += risk_analysis + "\n\n"

        content += """---

## 🚀 Success Metrics

"""
        # LLM generates success metrics
        success_metrics = self._generate_section_with_llm(
            "Success Metrics",
            f"Define success metrics for {project_name}. Include: KPIs (user acquisition, retention, engagement), technical metrics (performance, uptime), and business metrics (conversion, revenue if applicable). Be specific with target numbers.",
            context
        )
        content += success_metrics + "\n\n"

        try:
            file_path = os.path.join(self.project_dir, "plan.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating plan.md: {e}")
            return False

    def _generate_task_md(self, project: Dict, roadmap: Dict) -> bool:
        """Generate task.md file with LLM-generated detailed tasks."""
        # Get project info with fallbacks
        project_name = self._get_project_name(project)
        idea = project.get("idea", project.get("core_idea", project.get("description", "")))
        features = project.get("features", project.get("main_features", []))

        # Get tech_stack from project or load separately
        tech_stack = project.get("tech_stack", {})
        if not tech_stack:
            tech_stack = self.storage.load("tech_stack") or {}

        context = {
            "project_name": project_name,
            "idea": idea,
            "features": features if isinstance(features, list) else [features],
            "tech_stack": tech_stack
        }

        content = f"""# {project_name} - Task Breakdown

Generated by BOTUVIC on {datetime.now().strftime("%Y-%m-%d")}

---

## 📋 How to Use This File

| Step | Action |
|------|--------|
| 1 | Read `prd.md` to understand what you're building |
| 2 | Check `database.md` for schema details |
| 3 | Reference `backend.md` for API specs |
| 4 | Follow `frontend.md` for UI requirements |
| 5 | Check off `[ ]` boxes as you complete tasks |
| 6 | Update `progress-tracker.md` after each phase |

---

## 📊 Progress Overview

| Phase | Status | Tasks |
|-------|--------|-------|
| Setup & Infrastructure | ⬜ Not Started | 8 |
| Database & Models | ⬜ Not Started | 6 |
| Backend API | ⬜ Not Started | 10 |
| Frontend Core | ⬜ Not Started | 8 |
| Features & Integration | ⬜ Not Started | 10 |
| Testing & Deployment | ⬜ Not Started | 6 |

---

"""
        # LLM generates detailed tasks for each phase
        setup_tasks = self._generate_section_with_llm(
            "Setup Tasks",
            f"Generate a detailed task checklist for Phase 1: Setup & Infrastructure for {project_name}. Include 8-10 specific tasks with markdown checkboxes (- [ ]). Each task should have: task name, estimated time, and any dependencies. Include: environment setup, Git initialization, package installation, config files (.env, etc.), folder structure creation.",
            context
        )
        content += "## Phase 1: Setup & Infrastructure\n\n"
        content += setup_tasks + "\n\n---\n\n"

        db_tasks = self._generate_section_with_llm(
            "Database Tasks",
            f"Generate a detailed task checklist for Phase 2: Database & Models for {project_name}. Include 6-8 specific tasks with markdown checkboxes (- [ ]). Cover: database connection, schema creation, migrations, seed data, model definitions, relationships.",
            context
        )
        content += "## Phase 2: Database & Models\n\n"
        content += db_tasks + "\n\n---\n\n"

        backend_tasks = self._generate_section_with_llm(
            "Backend Tasks",
            f"Generate a detailed task checklist for Phase 3: Backend API for {project_name}. Include 10-12 specific tasks with markdown checkboxes (- [ ]). Cover: authentication routes, main feature endpoints, middleware setup, validation, error handling, API documentation.",
            context
        )
        content += "## Phase 3: Backend API\n\n"
        content += backend_tasks + "\n\n---\n\n"

        frontend_tasks = self._generate_section_with_llm(
            "Frontend Tasks",
            f"Generate a detailed task checklist for Phase 4: Frontend Core for {project_name}. Include 8-10 specific tasks with markdown checkboxes (- [ ]). Cover: project setup, routing, layout components, auth pages (login/register), navigation, state management, API service setup.",
            context
        )
        content += "## Phase 4: Frontend Core\n\n"
        content += frontend_tasks + "\n\n---\n\n"

        feature_tasks = self._generate_section_with_llm(
            "Feature Tasks",
            f"Generate a detailed task checklist for Phase 5: Features & Integration for {project_name}. Include 10-12 specific tasks with markdown checkboxes (- [ ]). Cover each main feature: {', '.join(features)}. For each: UI component, API integration, state management, error handling.",
            context
        )
        content += "## Phase 5: Features & Integration\n\n"
        content += feature_tasks + "\n\n---\n\n"

        deploy_tasks = self._generate_section_with_llm(
            "Deployment Tasks",
            f"Generate a detailed task checklist for Phase 6: Testing & Deployment for {project_name}. Include 6-8 specific tasks with markdown checkboxes (- [ ]). Cover: unit tests, integration tests, responsive design, performance optimization, production build, deployment to hosting, monitoring setup.",
            context
        )
        content += "## Phase 6: Testing & Deployment\n\n"
        content += deploy_tasks + "\n\n"

        content += """---

## 🎯 Quick Wins (Start Here)

These are the first 5 tasks to tackle:

1. - [ ] Clone repo and install dependencies
2. - [ ] Create `.env` file from `.env.example`
3. - [ ] Set up database connection
4. - [ ] Run database migrations
5. - [ ] Start development server

---

## 📝 Notes

Use this space for task-related notes, blockers, and decisions.

"""

        try:
            file_path = os.path.join(self.project_dir, "task.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating task.md: {e}")
            return False

    def _generate_env_example(self, project: Dict) -> bool:
        """Generate .env.example file."""
        # Try to get tech_stack from project, or load separately
        tech_stack = project.get("tech_stack", {})
        if not tech_stack:
            tech_stack = self.storage.load("tech_stack") or {}

        content = """# Environment Variables
# Copy this file to .env and fill in your values

# ============================================
# DATABASE
# ============================================
DATABASE_URL=your_database_connection_string

"""
        # Add based on tech stack
        db = tech_stack.get("database", {})
        db_name = db.get("name", "").lower() if isinstance(db, dict) else str(db).lower()

        if "supabase" in db_name:
            content += """# Supabase
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key

"""
        elif "firebase" in db_name:
            content += """# Firebase
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com

"""

        content += """# ============================================
# AUTHENTICATION
# ============================================
"""
        content += f"JWT_SECRET={secrets.token_hex(32)}\n"
        content += f"SESSION_SECRET={secrets.token_hex(32)}\n\n"

        # Check for storage
        storage = tech_stack.get("storage", {})
        storage_name = storage.get("name", "").lower() if isinstance(storage, dict) else str(storage).lower()

        if "s3" in storage_name or "aws" in storage_name:
            content += """# ============================================
# AWS S3 Storage
# ============================================
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name

"""
        elif "cloudinary" in storage_name:
            content += """# ============================================
# Cloudinary Storage
# ============================================
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

"""

        # Check for other tools and external tools
        other_tools = tech_stack.get("other_tools", [])
        external_tools = project.get("external_tools", [])
        if not external_tools:
            external_tools = self.storage.load("external_tools") or []

        # Combine all tools
        all_tools = list(other_tools) + list(external_tools)
        for tool in all_tools:
            tool_name = tool.get("name", "").lower() if isinstance(tool, dict) else str(tool).lower()

            if "stripe" in tool_name:
                content += """# ============================================
# Stripe Payments
# ============================================
STRIPE_PUBLIC_KEY=pk_test_your_public_key
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

"""
            elif "twilio" in tool_name:
                content += """# ============================================
# Twilio SMS
# ============================================
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

"""
            elif "sendgrid" in tool_name or "email" in tool_name:
                content += """# ============================================
# Email (SendGrid)
# ============================================
SENDGRID_API_KEY=your_sendgrid_api_key
EMAIL_FROM=noreply@yourdomain.com

"""
            elif "google" in tool_name and "map" in tool_name:
                content += """# ============================================
# Google Maps
# ============================================
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

"""
            elif "firebase" in tool_name or "fcm" in tool_name:
                content += """# ============================================
# Firebase Cloud Messaging
# ============================================
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id

"""
            elif "openai" in tool_name or "gpt" in tool_name:
                content += """# ============================================
# OpenAI
# ============================================
OPENAI_API_KEY=sk-your_openai_api_key

"""
            elif "pusher" in tool_name:
                content += """# ============================================
# Pusher (Realtime)
# ============================================
PUSHER_APP_ID=your_app_id
PUSHER_KEY=your_key
PUSHER_SECRET=your_secret
PUSHER_CLUSTER=us2

"""
            elif "algolia" in tool_name:
                content += """# ============================================
# Algolia Search
# ============================================
ALGOLIA_APP_ID=your_app_id
ALGOLIA_API_KEY=your_api_key
ALGOLIA_SEARCH_KEY=your_search_only_key

"""
            elif "mailgun" in tool_name:
                content += """# ============================================
# Mailgun
# ============================================
MAILGUN_API_KEY=your_api_key
MAILGUN_DOMAIN=your_domain.com

"""
            elif "redis" in tool_name:
                content += """# ============================================
# Redis
# ============================================
REDIS_URL=redis://localhost:6379

"""

        content += """# ============================================
# APPLICATION
# ============================================
NODE_ENV=development
PORT=8000
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
"""

        try:
            file_path = os.path.join(self.project_dir, ".env.example")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating .env.example: {e}")
            return False

    def _generate_gitignore(self, project: Dict) -> bool:
        """Generate .gitignore file."""
        tech_stack = project.get("tech_stack", {})

        content = """# Dependencies
node_modules/
__pycache__/
*.pyc
venv/
.venv/
env/

# Environment files
.env
.env.local
.env.*.local
*.env

# Build outputs
dist/
build/
.next/
out/

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Logs
logs/
*.log
npm-debug.log*

# Testing
coverage/
.nyc_output/
.pytest_cache/

# Misc
*.bak
*.tmp
.cache/

# OS files
Thumbs.db
.DS_Store

# Project specific
.botuvic/reports/
"""

        # Add based on tech stack
        backend = tech_stack.get("backend", {})
        backend_name = backend.get("name", "").lower() if isinstance(backend, dict) else str(backend).lower()

        if "python" in backend_name or "fastapi" in backend_name or "django" in backend_name:
            content += """
# Python specific
*.egg-info/
.eggs/
*.egg
pip-log.txt
.mypy_cache/
"""

        try:
            file_path = os.path.join(self.project_dir, ".gitignore")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating .gitignore: {e}")
            return False

    def _generate_readme(self, project: Dict) -> bool:
        """Generate README.md file."""
        project_name = self._get_project_name(project)
        idea = project.get("idea", "A new project")
        tech_stack = project.get("tech_stack", {})

        content = f"""# {project_name}

{idea}

## Tech Stack

"""
        for key, value in tech_stack.items():
            if isinstance(value, dict):
                content += f"- **{key.title()}**: {value.get('name', '')}\n"
            else:
                content += f"- **{key.title()}**: {value}\n"

        content += """
## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Database account (see tech stack)

### Installation

1. Clone the repository
```bash
git clone <your-repo-url>
cd """ + project_name.lower().replace(" ", "-") + """
```

2. Install dependencies
```bash
# Frontend
cd frontend
npm install

# Backend
cd ../backend
npm install  # or pip install -r requirements.txt
```

3. Set up environment variables
```bash
cp .env.example .env
# Fill in your credentials
```

4. Start development servers
```bash
# Backend
npm run dev

# Frontend (in another terminal)
cd frontend
npm run dev
```

## Project Structure

```
""" + project_name.lower().replace(" ", "-") + """/
├── frontend/          # Frontend application
├── backend/           # Backend API
├── database/          # Database migrations and seeds
├── .botuvic/          # BOTUVIC project files
├── plan.md            # Development plan
├── task.md            # Task checklist
└── README.md          # This file
```

## Development

See `task.md` for the complete task breakdown.

See `plan.md` for the full development plan.

## License

MIT

---

Built with BOTUVIC
"""

        try:
            file_path = os.path.join(self.project_dir, "README.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating README.md: {e}")
            return False

    def _generate_cursor_md(self, project: Dict, db_schema: Dict, backend_arch: Dict, frontend_design: Dict, roadmap: Dict) -> bool:
        """Generate cursor.md with Cursor-optimized prompts."""
        project_name = self._get_project_name(project)
        tech_stack = project.get("tech_stack", {})

        content = f"""# Cursor Instructions for {project_name}

This file contains optimized prompts for Cursor AI. Copy each prompt into Cursor when you reach that task.

## Project Context

Read plan.md first for full project details.

## Tech Stack
"""
        for key, value in tech_stack.items():
            if isinstance(value, dict):
                content += f"- {key.title()}: {value.get('name', '')}\n"
            else:
                content += f"- {key.title()}: {value}\n"

        content += """

---

## Phase 1: Database Setup

### Task 1.1: Create Database Tables

**Prompt for Cursor:**
```
Create SQL migration file to set up these tables:

"""
        if db_schema:
            tables = db_schema.get("tables", {})
            # Handle both list and dict formats
            if isinstance(tables, list):
                for table in tables:
                    if isinstance(table, dict):
                        table_name = table.get("name", "unknown")
                        table_info = table
                    else:
                        table_name = str(table)
                        table_info = {}
                    
                    content += f"{table_name} table:\n"
                    fields = table_info.get("fields", []) if isinstance(table_info, dict) else []
                    for field in fields:
                        if isinstance(field, dict):
                            content += f"- {field.get('name', '')} ({field.get('type', '')})"
                            if field.get("constraints"):
                                content += f" - {field.get('constraints')}"
                        else:
                            content += f"- {field}"
                        content += "\n"
                    content += "\n"
            else:
                # Dict format
            for table_name, table_info in tables.items():
                content += f"{table_name} table:\n"
                    fields = table_info.get("fields", []) if isinstance(table_info, dict) else []
                for field in fields:
                        if isinstance(field, dict):
                    content += f"- {field.get('name', '')} ({field.get('type', '')})"
                    if field.get("constraints"):
                        content += f" - {field.get('constraints')}"
                        else:
                            content += f"- {field}"
                    content += "\n"
                content += "\n"

        content += """
Add appropriate indexes and constraints.
```

### Task 1.2: Authentication Setup

**Prompt for Cursor:**
```
Set up authentication in src/services/auth.js with:
- signUp function (email, password)
- signIn function (email, password)
- signOut function
- getCurrentUser function
Use the database configured in .env
```

---

## Phase 2: Backend API

### Task 2.1: Server Setup

**Prompt for Cursor:**
```
Create backend server with:
- CORS enabled for localhost:3000
- JSON body parser
- Error handling middleware
- Health check endpoint at GET /health
- Listen on port from .env (default 8000)
```

### Task 2.2: API Routes

**Prompt for Cursor:**
```
Create API routes based on this structure:

"""
        if backend_arch:
            endpoints = backend_arch.get("endpoints", {})
            for category, eps in endpoints.items():
                content += f"{category}:\n"
                if isinstance(eps, list):
                    for ep in eps:
                        if isinstance(ep, dict):
                        content += f"- {ep.get('method', 'GET')} {ep.get('path', '')} - {ep.get('description', '')}\n"
                        else:
                            content += f"- {ep}\n"
                content += "\n"

        content += """
Add proper error handling and validation for each route.
```

---

## Phase 3: Frontend

### Task 3.1: Project Setup

**Prompt for Cursor:**
```
Initialize React project with:
- Vite as build tool
- React Router for routing
- Tailwind CSS for styling
- Axios for API calls
Create base folder structure: components/, pages/, services/, hooks/, utils/
```

### Task 3.2: Layout Components

**Prompt for Cursor:**
```
Create layout components:
- Navbar with logo and navigation links
- Footer with copyright
- MainLayout wrapping pages with Navbar and Footer
- AuthLayout for login/signup pages (centered, no navbar)
```

### Task 3.3: Authentication Pages

**Prompt for Cursor:**
```
Create authentication pages:
- Login page with email/password form
- Signup page with email/password/confirm password
- Use the auth service to call backend
- Redirect to home on success
- Show error messages on failure
```

---

## Phase 4: Core Features

"""
        # Add feature-specific prompts based on project
        features = project.get("features", [])
        for i, feature in enumerate(features, 1):
            content += f"""### Task 4.{i}: {feature}

**Prompt for Cursor:**
```
Implement {feature}:
- Create necessary components
- Add API integration
- Handle loading and error states
- Make it responsive
```

"""

        content += """---

## Phase 5: Polish & Deploy

### Task 5.1: Loading States

**Prompt for Cursor:**
```
Add loading states to all pages:
- Skeleton loaders for content
- Spinner for buttons during submit
- Page loading indicator
```

### Task 5.2: Error Handling

**Prompt for Cursor:**
```
Add comprehensive error handling:
- Toast notifications for errors
- Error boundaries for React
- 404 page
- Server error page
- Form validation errors
```

### Task 5.3: Deployment

**Prompt for Cursor:**
```
Prepare for deployment:
- Add production environment variables
- Configure build scripts
- Add deployment configuration for [platform]
- Test production build locally
```

---

## Tips for Using Cursor

1. Open the relevant file before pasting the prompt
2. Use Cmd+K (Mac) or Ctrl+K (Windows) to open Cursor chat
3. If output is incomplete, say "continue"
4. Review generated code before accepting
5. Test each feature before moving to next task

---

Generated by BOTUVIC
"""

        try:
            file_path = os.path.join(self.project_dir, "cursor.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating cursor.md: {e}")
            return False

    def _generate_claude_code_md(self, project: Dict, db_schema: Dict, backend_arch: Dict, frontend_design: Dict, roadmap: Dict) -> bool:
        """Generate claude-code.md with Claude Code optimized instructions."""
        project_name = self._get_project_name(project)
        idea = project.get("idea", "")
        tech_stack = project.get("tech_stack", {})

        content = f"""# Claude Code Instructions for {project_name}

This file contains instructions optimized for Claude Code (Cline). Follow these step by step.

## Project Context

{idea}

## Tech Stack
"""
        for key, value in tech_stack.items():
            if isinstance(value, dict):
                content += f"- {key.title()}: {value.get('name', '')}\n"
            else:
                content += f"- {key.title()}: {value}\n"

        content += """

## Important Files

- plan.md - Full project plan and specifications
- task.md - Task checklist (mark tasks as you complete)
- .env.example - Required environment variables

## Development Approach

1. Read plan.md first to understand the full project
2. Follow tasks in task.md in order
3. Test each feature before moving to next
4. Ask for approval before making significant changes
5. Commit after each major feature

---

## Phase 1: Setup

### Step 1: Database

1. Read the database schema in plan.md
2. Create migration file in database/migrations/
3. Run migration to create tables
4. Test with sample data

### Step 2: Environment

1. Copy .env.example to .env
2. Fill in database credentials
3. Generate secrets for JWT_SECRET and SESSION_SECRET
4. Verify connection works

---

## Phase 2: Backend

### Step 1: Initialize Server

Create backend server with this structure:
```
backend/
├── src/
│   ├── routes/
│   ├── controllers/
│   ├── middleware/
│   ├── services/
│   └── utils/
├── server.js
└── package.json
```

Requirements:
- Express.js (or FastAPI if Python)
- CORS for frontend
- JSON body parsing
- Error handling middleware

### Step 2: Authentication Routes

Create auth routes:
- POST /api/auth/signup
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me

Use bcrypt for passwords, JWT for tokens.

### Step 3: Feature Routes

Create routes as defined in plan.md under "Backend API Endpoints".

---

## Phase 3: Frontend

### Step 1: Initialize Project

Create React app with:
- Vite
- React Router
- Tailwind CSS

Structure:
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/
│   │   └── features/
│   ├── pages/
│   ├── hooks/
│   ├── services/
│   └── utils/
├── App.jsx
└── main.jsx
```

### Step 2: API Client

Create API client in services/api.js:
- Axios instance with base URL
- Auth token interceptor
- Error handling

### Step 3: Pages

Build pages as defined in plan.md under "Frontend Pages & Flows".

---

## Phase 4: Features

Implement each feature from task.md:
1. Build UI component
2. Connect to API
3. Handle loading/error states
4. Test thoroughly
5. Mark task complete in task.md

---

## Phase 5: Deploy

1. Test production build locally
2. Set up deployment platform
3. Configure environment variables
4. Deploy backend first
5. Deploy frontend
6. Test live site

---

## Tips for Claude Code

1. Read existing files before modifying
2. Follow project patterns already established
3. Ask clarifying questions if unsure
4. Test after each change
5. Keep changes focused and atomic

---

Generated by BOTUVIC
"""

        try:
            file_path = os.path.join(self.project_dir, "claude-code.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating claude-code.md: {e}")
            return False

    def _generate_dev_guide(self, project: Dict, db_schema: Dict, backend_arch: Dict, frontend_design: Dict, roadmap: Dict) -> bool:
        """Generate development-guide.md for manual coders."""
        project_name = self._get_project_name(project)
        idea = project.get("idea", "")
        tech_stack = project.get("tech_stack", {})

        content = f"""# Development Guide for {project_name}

This guide provides step-by-step instructions for building this project manually.

## Project Overview

{idea}

## Prerequisites

- Node.js 18+ installed
- Code editor (VS Code recommended)
- Git installed
- Database account created

## Tech Stack
"""
        for key, value in tech_stack.items():
            if isinstance(value, dict):
                content += f"- {key.title()}: {value.get('name', '')}\n"
            else:
                content += f"- {key.title()}: {value}\n"

        content += """

---

## Initial Setup

### Step 1: Create Project Directory

```bash
mkdir """ + project_name.lower().replace(" ", "-") + """
cd """ + project_name.lower().replace(" ", "-") + """
```

### Step 2: Initialize Git

```bash
git init
```

### Step 3: Set Up Environment

```bash
cp .env.example .env
```

Fill in your credentials in .env file.

---

## Backend Setup

### Step 1: Create Backend Folder

```bash
mkdir -p backend/src/{routes,controllers,middleware,services,utils}
cd backend
```

### Step 2: Initialize Project

```bash
npm init -y
npm install express cors dotenv bcrypt jsonwebtoken
npm install -D nodemon
```

### Step 3: Create Server

Create `server.js`:

```javascript
const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();

// Middleware
app.use(cors({ origin: process.env.FRONTEND_URL }));
app.use(express.json());

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ error: 'Internal server error' });
});

const PORT = process.env.PORT || 8000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

### Step 4: Add Scripts

In `package.json`:

```json
{
  "scripts": {
    "dev": "nodemon server.js",
    "start": "node server.js"
  }
}
```

### Step 5: Create Routes

See plan.md for all required endpoints. Create each route in `src/routes/`.

---

## Frontend Setup

### Step 1: Create Frontend

```bash
cd ..
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install react-router-dom axios
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### Step 2: Configure Tailwind

In `tailwind.config.js`:

```javascript
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

In `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Step 3: Create Folder Structure

```bash
mkdir -p src/{components/{ui,layout,features},pages,hooks,services,utils}
```

### Step 4: Create API Service

Create `src/services/api.js`:

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

---

## Building Features

Follow task.md for the complete task breakdown. For each task:

1. **Read the requirements** in plan.md
2. **Create the component/route**
3. **Test it works**
4. **Check off the task** in task.md
5. **Commit your changes**

```bash
git add .
git commit -m "feat: [what you built]"
```

---

## Common Commands

### Backend
```bash
cd backend
npm run dev      # Start development server
npm start        # Start production server
```

### Frontend
```bash
cd frontend
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
```

---

## Troubleshooting

### CORS Errors
- Check FRONTEND_URL in backend .env
- Ensure backend is running

### Database Connection
- Verify DATABASE_URL is correct
- Check if database service is running

### Auth Not Working
- Check JWT_SECRET is set
- Verify token is being sent in headers

---

## Resources

- React Docs: https://react.dev
- Express Docs: https://expressjs.com
- Tailwind CSS: https://tailwindcss.com
- See plan.md for project-specific details

---

Generated by BOTUVIC
"""

        try:
            file_path = os.path.join(self.project_dir, "development-guide.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating development-guide.md: {e}")
            return False

    def generate_project_structure(self, tech_stack: Dict) -> Dict[str, Any]:
        """Generate complete project folder structure."""

        frontend = tech_stack.get("frontend", {})
        backend = tech_stack.get("backend", {})

        frontend_name = frontend.get("name", "react").lower() if isinstance(frontend, dict) else str(frontend).lower()
        backend_name = backend.get("name", "express").lower() if isinstance(backend, dict) else str(backend).lower()

        structure = {
            "folders": [],
            "files": []
        }

        # Frontend structure
        if "react" in frontend_name or "next" in frontend_name or "vue" in frontend_name:
            structure["folders"].extend([
                "frontend/src/components/ui",
                "frontend/src/components/layout",
                "frontend/src/components/features",
                "frontend/src/pages",
                "frontend/src/hooks",
                "frontend/src/services",
                "frontend/src/store",
                "frontend/src/utils",
                "frontend/public"
            ])

        # Backend structure
        if "express" in backend_name or "node" in backend_name:
            structure["folders"].extend([
                "backend/src/routes",
                "backend/src/controllers",
                "backend/src/models",
                "backend/src/middleware",
                "backend/src/services",
                "backend/src/utils"
            ])
        elif "fastapi" in backend_name or "python" in backend_name:
            structure["folders"].extend([
                "backend/app/routers",
                "backend/app/models",
                "backend/app/schemas",
                "backend/app/services",
                "backend/app/utils"
            ])

        # Database
        structure["folders"].extend([
            "database/migrations",
            "database/seeds"
        ])

        # BOTUVIC
        structure["folders"].extend([
            ".botuvic/reports"
        ])

        return structure

    def create_base_files(self, tech_stack: Dict) -> Dict[str, bool]:
        """Create base files with starter code."""
        results = {}

        frontend = tech_stack.get("frontend", {})
        backend = tech_stack.get("backend", {})

        frontend_name = frontend.get("name", "react").lower() if isinstance(frontend, dict) else str(frontend).lower()
        backend_name = backend.get("name", "express").lower() if isinstance(backend, dict) else str(backend).lower()

        # Frontend files
        if "react" in frontend_name:
            results["frontend/package.json"] = self._write_file("frontend/package.json", """{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}""")

            results["frontend/vite.config.js"] = self._write_file("frontend/vite.config.js", """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000
  }
})""")

            results["frontend/tailwind.config.js"] = self._write_file("frontend/tailwind.config.js", """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}""")

            results["frontend/postcss.config.js"] = self._write_file("frontend/postcss.config.js", """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}""")

            results["frontend/index.html"] = self._write_file("frontend/index.html", """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>""")

            results["frontend/src/main.jsx"] = self._write_file("frontend/src/main.jsx", """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)""")

            results["frontend/src/App.jsx"] = self._write_file("frontend/src/App.jsx", """import { BrowserRouter, Routes, Route } from 'react-router-dom'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<div>Welcome! Start building...</div>} />
      </Routes>
    </BrowserRouter>
  )
}

export default App""")

            results["frontend/src/index.css"] = self._write_file("frontend/src/index.css", """@tailwind base;
@tailwind components;
@tailwind utilities;""")

            results["frontend/src/services/api.js"] = self._write_file("frontend/src/services/api.js", """import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;""")

            results["frontend/.env.example"] = self._write_file("frontend/.env.example", """VITE_API_URL=http://localhost:8000""")

        # Backend files
        if "express" in backend_name or "node" in backend_name:
            results["backend/package.json"] = self._write_file("backend/package.json", """{
  "name": "backend",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "dev": "nodemon server.js",
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "bcrypt": "^5.1.1",
    "jsonwebtoken": "^9.0.2"
  },
  "devDependencies": {
    "nodemon": "^3.0.2"
  }
}""")

            results["backend/server.js"] = self._write_file("backend/server.js", """const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();

// Middleware
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
}));
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Routes will be added here
// app.use('/api/auth', require('./src/routes/auth'));

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

const PORT = process.env.PORT || 8000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});""")

            results["backend/.env.example"] = self._write_file("backend/.env.example", f"""PORT=8000
FRONTEND_URL=http://localhost:3000
DATABASE_URL=your_database_url
JWT_SECRET={secrets.token_hex(32)}
""")

        elif "fastapi" in backend_name or "python" in backend_name:
            results["backend/requirements.txt"] = self._write_file("backend/requirements.txt", """fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
bcrypt==4.1.1
python-jose==3.3.0
passlib==1.7.4
sqlalchemy==2.0.23
""")

            results["backend/main.py"] = self._write_file("backend/main.py", """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Add routers here
# from app.routers import auth
# app.include_router(auth.router, prefix="/api/auth")
""")

            results["backend/.env.example"] = self._write_file("backend/.env.example", f"""FRONTEND_URL=http://localhost:3000
DATABASE_URL=your_database_url
JWT_SECRET={secrets.token_hex(32)}
""")

        # Database files - only create placeholder if no real schema exists
        schema_path = os.path.join(self.project_dir, "database/schema.sql")
        if not os.path.exists(schema_path) or os.path.getsize(schema_path) < 500:
            # Only write placeholder if file doesn't exist or is just a placeholder
        results["database/schema.sql"] = self._write_file("database/schema.sql", """-- Database Schema
-- Run this file to create your tables

-- Example:
-- CREATE TABLE users (
--   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   email VARCHAR(255) UNIQUE NOT NULL,
--   password_hash VARCHAR(255) NOT NULL,
--   created_at TIMESTAMP DEFAULT NOW()
-- );
""")
        else:
            results["database/schema.sql"] = True  # Already exists with real content

        return results

    def create_backend_files(self) -> Dict[str, bool]:
        """
        Create complete backend structure with all files (100%).

        Returns:
            Dict of file paths to success status
        """
        results = {}

        # Load project data (try multiple sources)
        project = self.storage.load("project") or {}
        tech_stack = self.storage.load("tech_stack") or project.get("tech_stack", {})
        backend_info = tech_stack.get("backend", {})
        database_info = tech_stack.get("database", {})
        backend_architecture = self.storage.load("backend_architecture") or {}
        db_schema = self.storage.load("database_schema") or {}

        backend_name = backend_info.get("name", "express").lower() if isinstance(backend_info, dict) else str(backend_info).lower()
        db_name = database_info.get("name", "postgresql").lower() if isinstance(database_info, dict) else str(database_info).lower()

        from rich.console import Console
        console = Console()
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Creating backend:[/#F1F5F9] {backend_name}")

        # Detect backend type
        if "node" in backend_name or "express" in backend_name:
            results.update(self._create_nodejs_backend(backend_architecture, db_name))
        elif "fastapi" in backend_name:
            results.update(self._create_fastapi_backend(backend_architecture, db_name))
        elif "django" in backend_name:
            results.update(self._create_django_backend(backend_architecture, db_name))
        elif "flask" in backend_name:
            results.update(self._create_flask_backend(backend_architecture, db_name))
        elif "go" in backend_name or "gin" in backend_name or "golang" in backend_name:
            results.update(self._create_go_backend(backend_architecture, db_name))
        elif "ruby" in backend_name or "rails" in backend_name:
            results.update(self._create_rails_backend(backend_architecture, db_name))
        elif "java" in backend_name or "spring" in backend_name:
            results.update(self._create_spring_backend(backend_architecture, db_name))
        elif "php" in backend_name or "laravel" in backend_name:
            results.update(self._create_laravel_backend(backend_architecture, db_name))
        elif "dotnet" in backend_name or ".net" in backend_name or "asp.net" in backend_name or "c#" in backend_name:
            results.update(self._create_dotnet_backend(backend_architecture, db_name))
        elif "python" in backend_name:
            # Default Python to FastAPI
            results.update(self._create_fastapi_backend(backend_architecture, db_name))
        else:
            # Default to Node.js/Express
            results.update(self._create_nodejs_backend(backend_architecture, db_name))

        # Create backend.md documentation
        backend_md_content = self._generate_backend_md(backend_name, db_name, backend_architecture)
        results["backend/backend.md"] = self._write_file("backend/backend.md", backend_md_content)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/backend.md ✓")

        return results

    def _create_nodejs_backend(self, architecture: Dict, db_name: str) -> Dict[str, bool]:
        """Create Node.js/Express backend with all files DYNAMICALLY from architecture."""
        results = {}
        from rich.console import Console
        console = Console()

        # Create folders
        folders = [
            "backend/src/routes",
            "backend/src/controllers",
            "backend/src/services",
            "backend/src/middleware",
            "backend/src/models",
            "backend/src/config",
            "backend/src/utils"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created backend folders[/#F1F5F9] ✓")

        # Get routes from architecture (dynamic!)
        routes = architecture.get("routes", ["/auth"])
        endpoints_raw = architecture.get("endpoints", {})

        # Normalize endpoints - ensure it's a dict
        if isinstance(endpoints_raw, list):
            # Convert list of endpoints to dict grouped by first path segment
            endpoints = {}
            for ep in endpoints_raw:
                if isinstance(ep, dict):
                    path = ep.get("path", "/").strip("/").split("/")[0] or "api"
                    if path not in endpoints:
                        endpoints[path] = []
                    endpoints[path].append(ep)
                elif isinstance(ep, str):
                    path = ep.strip("/").split("/")[0] or "api"
                    if path not in endpoints:
                        endpoints[path] = []
        else:
            endpoints = endpoints_raw if isinstance(endpoints_raw, dict) else {}

        # Normalize routes - ensure they're clean names
        route_names = []
        for route in routes:
            name = route.strip("/").split("/")[0] if isinstance(route, str) else "auth"
            if name and name not in route_names:
                route_names.append(name)

        # Ensure auth is always included
        if "auth" not in route_names:
            route_names.insert(0, "auth")

        # Detect database client package
        if "supabase" in db_name:
            db_package = '"@supabase/supabase-js": "^2.39.0"'
        elif "mongo" in db_name:
            db_package = '"mongodb": "^6.3.0"'
        elif "postgres" in db_name:
            db_package = '"pg": "^8.11.0"'
        elif "mysql" in db_name:
            db_package = '"mysql2": "^3.6.0"'
        else:
            db_package = '"pg": "^8.11.0"'

        # package.json
        package_json = f"""{{
  "name": "backend",
  "version": "1.0.0",
  "type": "module",
  "description": "Backend API",
  "main": "server.js",
  "scripts": {{
    "dev": "nodemon server.js",
    "start": "node server.js",
    "test": "echo \\"Error: no test specified\\" && exit 1"
  }},
  "dependencies": {{
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    {db_package},
    "bcrypt": "^5.1.1",
    "jsonwebtoken": "^9.0.2",
    "uuid": "^9.0.0"
  }},
  "devDependencies": {{
    "nodemon": "^3.0.2"
  }}
}}"""
        results["backend/package.json"] = self._write_file("backend/package.json", package_json)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/package.json ✓")

        # Generate dynamic route imports and uses
        route_imports = "\n".join([f"import {name}Routes from './src/routes/{name}.js'" for name in route_names])
        route_uses = "\n".join([f"app.use('/api/{name}', {name}Routes)" for name in route_names])

        # server.js - DYNAMIC
        server_js = f"""import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'

// Import routes
{route_imports}

dotenv.config()

const app = express()
const PORT = process.env.PORT || 8000

// Middleware
app.use(cors())
app.use(express.json())

// Routes
{route_uses}

// Health check
app.get('/health', (req, res) => {{
  res.json({{ status: 'healthy', timestamp: new Date().toISOString() }})
}})

// Error handling middleware
app.use((err, req, res, next) => {{
  console.error(err.stack)
  res.status(500).json({{ error: 'Something went wrong!', message: err.message }})
}})

app.listen(PORT, () => {{
  console.log(`✓ Server running on http://localhost:${{PORT}}`)
}})
"""
        results["backend/server.js"] = self._write_file("backend/server.js", server_js)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/server.js ✓")

        # .env.example
        env_example = self._generate_backend_env_example(db_name)
        results["backend/.env.example"] = self._write_file("backend/.env.example", env_example)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/.env.example ✓")

        # .gitignore
        gitignore = """node_modules/
.env
*.log
.DS_Store
"""
        results["backend/.gitignore"] = self._write_file("backend/.gitignore", gitignore)

        # Create auth middleware (always needed)
        auth_middleware = """import jwt from 'jsonwebtoken'

export const authenticate = (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(' ')[1]

    if (!token) {
      return res.status(401).json({ error: 'No token provided' })
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET)
    req.user = decoded
    next()
  } catch (error) {
    res.status(401).json({ error: 'Invalid token' })
  }
}

export const optionalAuth = (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(' ')[1]
    if (token) {
      const decoded = jwt.verify(token, process.env.JWT_SECRET)
      req.user = decoded
    }
    next()
  } catch (error) {
    next()
  }
}
"""
        results["backend/src/middleware/auth.js"] = self._write_file("backend/src/middleware/auth.js", auth_middleware)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/src/middleware/auth.js ✓")

        # Database config
        db_config = self._generate_db_config(db_name)
        results["backend/src/config/database.js"] = self._write_file("backend/src/config/database.js", db_config)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/src/config/database.js ✓")

        # Create route and controller for EACH route dynamically
        for route_name in route_names:
            route_endpoints = endpoints.get(route_name, [])

            # Generate route file
            route_content = self._generate_express_route(route_name, route_endpoints)
            results[f"backend/src/routes/{route_name}.js"] = self._write_file(f"backend/src/routes/{route_name}.js", route_content)
            console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/src/routes/{route_name}.js ✓")

            # Generate controller file
            controller_content = self._generate_express_controller(route_name, route_endpoints)
            results[f"backend/src/controllers/{route_name}Controller.js"] = self._write_file(f"backend/src/controllers/{route_name}Controller.js", controller_content)
            console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/src/controllers/{route_name}Controller.js ✓")

            # Generate service file
            service_content = self._generate_express_service(route_name)
            results[f"backend/src/services/{route_name}Service.js"] = self._write_file(f"backend/src/services/{route_name}Service.js", service_content)
            console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/src/services/{route_name}Service.js ✓")

        # README.md - DYNAMIC
        endpoint_docs = self._generate_endpoint_docs(route_names, endpoints)
        readme = f"""# Backend API

## Setup

1. Install dependencies:
```bash
npm install
```

2. Copy .env.example to .env and fill in your credentials:
```bash
cp .env.example .env
```

3. Run development server:
```bash
npm run dev
```

Server will start at http://localhost:8000

## API Endpoints

{endpoint_docs}

### Health Check
- GET `/health` - Check if server is running

## Development

See `backend.md` for detailed backend setup instructions.
"""
        results["backend/README.md"] = self._write_file("backend/README.md", readme)

        return results

    def _generate_express_route(self, name: str, endpoints: list) -> str:
        """Generate Express route file dynamically."""
        capitalized = name.capitalize()

        # Default CRUD endpoints if none specified
        if not endpoints:
            if name == "auth":
                endpoints = [
                    {"method": "POST", "path": "/register", "description": "Register new user"},
                    {"method": "POST", "path": "/login", "description": "Login user"},
                    {"method": "POST", "path": "/logout", "description": "Logout user"},
                    {"method": "GET", "path": "/me", "description": "Get current user"}
                ]
            else:
                endpoints = [
                    {"method": "GET", "path": "/", "description": f"List all {name}"},
                    {"method": "POST", "path": "/", "description": f"Create {name}"},
                    {"method": "GET", "path": "/:id", "description": f"Get {name} by ID"},
                    {"method": "PUT", "path": "/:id", "description": f"Update {name}"},
                    {"method": "DELETE", "path": "/:id", "description": f"Delete {name}"}
                ]

        # Generate method names from endpoints
        methods = []
        route_lines = []

        for ep in endpoints:
            if isinstance(ep, dict):
                method = ep.get("method", "GET").upper()
                path = ep.get("path", "/")
                desc = ep.get("description", "")
            else:
                continue

            # Generate method name
            method_name = self._endpoint_to_method_name(method, path, name)
            methods.append(method_name)

            # Determine if auth required
            needs_auth = name != "auth" or path in ["/logout", "/me"]
            auth_middleware = ", authenticate" if needs_auth else ""

            route_lines.append(f"router.{method.lower()}('{path}'{auth_middleware}, {method_name})")

        methods_import = ", ".join(methods)
        routes_code = "\n".join(route_lines)

        return f"""import express from 'express'
import {{ {methods_import} }} from '../controllers/{name}Controller.js'
import {{ authenticate }} from '../middleware/auth.js'

const router = express.Router()

{routes_code}

export default router
"""

    def _generate_express_controller(self, name: str, endpoints: list) -> str:
        """Generate Express controller file dynamically."""
        capitalized = name.capitalize()

        # Default CRUD endpoints if none specified
        if not endpoints:
            if name == "auth":
                endpoints = [
                    {"method": "POST", "path": "/register"},
                    {"method": "POST", "path": "/login"},
                    {"method": "POST", "path": "/logout"},
                    {"method": "GET", "path": "/me"}
                ]
            else:
                endpoints = [
                    {"method": "GET", "path": "/"},
                    {"method": "POST", "path": "/"},
                    {"method": "GET", "path": "/:id"},
                    {"method": "PUT", "path": "/:id"},
                    {"method": "DELETE", "path": "/:id"}
                ]

        # Generate controller methods
        controller_methods = []

        for ep in endpoints:
            if isinstance(ep, dict):
                method = ep.get("method", "GET").upper()
                path = ep.get("path", "/")
            else:
                continue

            method_name = self._endpoint_to_method_name(method, path, name)
            method_code = self._generate_controller_method(name, method_name, method, path)
            controller_methods.append(method_code)

        imports = """import bcrypt from 'bcrypt'
import jwt from 'jsonwebtoken'
// import { db } from '../config/database.js'
""" if name == "auth" else """// import { db } from '../config/database.js'
"""

        return f"""{imports}
{chr(10).join(controller_methods)}
"""

    def _generate_controller_method(self, resource: str, method_name: str, http_method: str, path: str) -> str:
        """Generate a single controller method."""
        capitalized = resource.capitalize()

        # Auth-specific methods
        if resource == "auth":
            if method_name == "register":
                return """export const register = async (req, res) => {
  try {
    const { email, password, name } = req.body

    // TODO: Check if user exists in database
    // const existingUser = await db.query('SELECT * FROM users WHERE email = $1', [email])
    // if (existingUser.rows.length > 0) {
    //   return res.status(400).json({ error: 'User already exists' })
    // }

    const hashedPassword = await bcrypt.hash(password, 10)

    // TODO: Create user in database
    // const result = await db.query(
    //   'INSERT INTO users (email, password_hash, name) VALUES ($1, $2, $3) RETURNING id, email, name',
    //   [email, hashedPassword, name]
    // )

    res.status(201).json({
      success: true,
      message: 'User registered successfully'
    })
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
}
"""
            elif method_name == "login":
                return """export const login = async (req, res) => {
  try {
    const { email, password } = req.body

    // TODO: Find user in database
    // const result = await db.query('SELECT * FROM users WHERE email = $1', [email])
    // const user = result.rows[0]
    // if (!user) {
    //   return res.status(401).json({ error: 'Invalid credentials' })
    // }

    // TODO: Compare password
    // const validPassword = await bcrypt.compare(password, user.password_hash)
    // if (!validPassword) {
    //   return res.status(401).json({ error: 'Invalid credentials' })
    // }

    const token = jwt.sign(
      { userId: 'user_id_here', email },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    )

    res.json({
      success: true,
      token,
      user: { email }
    })
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
}
"""
            elif method_name == "logout":
                return """export const logout = async (req, res) => {
  try {
    // TODO: Invalidate token if using token blacklist
    res.json({ success: true, message: 'Logged out successfully' })
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
}
"""
            elif method_name == "getMe":
                return """export const getMe = async (req, res) => {
  try {
    // User info is in req.user (set by auth middleware)
    // TODO: Fetch full user data from database
    // const result = await db.query('SELECT id, email, name FROM users WHERE id = $1', [req.user.userId])
    res.json({ success: true, user: req.user })
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
}
"""

        # Generic CRUD methods
        if "getAll" in method_name or (http_method == "GET" and path == "/"):
            return f"""export const {method_name} = async (req, res) => {{
  try {{
    // TODO: Fetch all {resource} from database
    // const result = await db.query('SELECT * FROM {resource}')
    // res.json({{ success: true, data: result.rows }})

    res.json({{
      success: true,
      data: [],
      message: 'List all {resource}'
    }})
  }} catch (error) {{
    res.status(500).json({{ error: error.message }})
  }}
}}
"""
        elif "create" in method_name or (http_method == "POST" and path == "/"):
            return f"""export const {method_name} = async (req, res) => {{
  try {{
    const data = req.body
    const userId = req.user?.userId

    // TODO: Create {resource} in database
    // const result = await db.query(
    //   'INSERT INTO {resource} (...) VALUES (...) RETURNING *',
    //   [...]
    // )

    res.status(201).json({{
      success: true,
      message: '{capitalized} created successfully',
      data: {{ ...data, id: 'new_id', createdBy: userId }}
    }})
  }} catch (error) {{
    res.status(500).json({{ error: error.message }})
  }}
}}
"""
        elif "getById" in method_name or "getOne" in method_name or (http_method == "GET" and ":id" in path):
            return f"""export const {method_name} = async (req, res) => {{
  try {{
    const {{ id }} = req.params

    // TODO: Fetch {resource} by ID from database
    // const result = await db.query('SELECT * FROM {resource} WHERE id = $1', [id])
    // if (result.rows.length === 0) {{
    //   return res.status(404).json({{ error: '{capitalized} not found' }})
    // }}

    res.json({{
      success: true,
      data: {{ id, name: 'Sample {capitalized}' }}
    }})
  }} catch (error) {{
    res.status(500).json({{ error: error.message }})
  }}
}}
"""
        elif "update" in method_name or http_method == "PUT":
            return f"""export const {method_name} = async (req, res) => {{
  try {{
    const {{ id }} = req.params
    const data = req.body
    const userId = req.user?.userId

    // TODO: Update {resource} in database
    // const result = await db.query(
    //   'UPDATE {resource} SET ... WHERE id = $1 RETURNING *',
    //   [id, ...]
    // )

    res.json({{
      success: true,
      message: '{capitalized} updated successfully',
      data: {{ id, ...data, updatedBy: userId }}
    }})
  }} catch (error) {{
    res.status(500).json({{ error: error.message }})
  }}
}}
"""
        elif "delete" in method_name or http_method == "DELETE":
            return f"""export const {method_name} = async (req, res) => {{
  try {{
    const {{ id }} = req.params

    // TODO: Delete {resource} from database
    // await db.query('DELETE FROM {resource} WHERE id = $1', [id])

    res.json({{
      success: true,
      message: '{capitalized} deleted successfully'
    }})
  }} catch (error) {{
    res.status(500).json({{ error: error.message }})
  }}
}}
"""
        else:
            # Generic method
            return f"""export const {method_name} = async (req, res) => {{
  try {{
    // TODO: Implement {method_name} logic
    res.json({{
      success: true,
      message: '{method_name} executed'
    }})
  }} catch (error) {{
    res.status(500).json({{ error: error.message }})
  }}
}}
"""

    def _generate_express_service(self, name: str) -> str:
        """Generate Express service file."""
        capitalized = name.capitalize()

        return f"""// {capitalized} Service
// Business logic for {name} operations

// import {{ db }} from '../config/database.js'

export const {name}Service = {{
  async getAll(filters = {{}}) {{
    // TODO: Implement with database
    // const result = await db.query('SELECT * FROM {name}')
    // return result.rows
    return []
  }},

  async getById(id) {{
    // TODO: Implement with database
    // const result = await db.query('SELECT * FROM {name} WHERE id = $1', [id])
    // return result.rows[0]
    return null
  }},

  async create(data, userId) {{
    // TODO: Implement with database
    // const result = await db.query(
    //   'INSERT INTO {name} (...) VALUES (...) RETURNING *',
    //   [...]
    // )
    // return result.rows[0]
    return {{ id: 'new_id', ...data, createdBy: userId }}
  }},

  async update(id, data, userId) {{
    // TODO: Implement with database
    // const result = await db.query(
    //   'UPDATE {name} SET ... WHERE id = $1 RETURNING *',
    //   [id, ...]
    // )
    // return result.rows[0]
    return {{ id, ...data, updatedBy: userId }}
  }},

  async delete(id) {{
    // TODO: Implement with database
    // await db.query('DELETE FROM {name} WHERE id = $1', [id])
    return true
  }}
}}
"""

    def _endpoint_to_method_name(self, method: str, path: str, resource: str) -> str:
        """Convert HTTP method + path to controller method name."""
        method = method.upper()
        path = path.strip("/")

        # Auth-specific naming
        if resource == "auth":
            if "register" in path:
                return "register"
            elif "login" in path:
                return "login"
            elif "logout" in path:
                return "logout"
            elif "me" in path:
                return "getMe"

        # Generic CRUD naming
        if method == "GET" and (path == "" or path == "/"):
            return f"getAll{resource.capitalize()}"
        elif method == "GET" and ":id" in path:
            return f"get{resource.capitalize()}ById"
        elif method == "POST" and (path == "" or path == "/"):
            return f"create{resource.capitalize()}"
        elif method == "PUT" and ":id" in path:
            return f"update{resource.capitalize()}"
        elif method == "DELETE" and ":id" in path:
            return f"delete{resource.capitalize()}"
        else:
            # Custom endpoint - extract name from path
            clean_path = path.replace("/", "_").replace(":", "").replace("-", "_")
            return f"{method.lower()}{clean_path.capitalize()}" if clean_path else method.lower()

    def _generate_db_config(self, db_name: str) -> str:
        """Generate database config file."""
        if "postgres" in db_name:
            return """import pg from 'pg'
const { Pool } = pg

export const db = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
})

// Test connection
db.query('SELECT NOW()', (err, res) => {
  if (err) {
    console.error('Database connection error:', err)
  } else {
    console.log('✓ Database connected')
  }
})

export default db
"""
        elif "mongo" in db_name:
            return """import { MongoClient } from 'mongodb'

const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017'
const client = new MongoClient(uri)

let db = null

export async function connectDB() {
  try {
    await client.connect()
    db = client.db(process.env.DB_NAME || 'myapp')
    console.log('✓ MongoDB connected')
    return db
  } catch (error) {
    console.error('MongoDB connection error:', error)
    throw error
  }
}

export function getDB() {
  if (!db) {
    throw new Error('Database not connected. Call connectDB first.')
  }
  return db
}

export default { connectDB, getDB }
"""
        else:
            return """import pg from 'pg'
const { Pool } = pg

export const db = new Pool({
  connectionString: process.env.DATABASE_URL
})

export default db
"""

    def _generate_endpoint_docs(self, route_names: list, endpoints: dict) -> str:
        """Generate endpoint documentation for README."""
        docs = []

        for name in route_names:
            capitalized = name.capitalize()
            docs.append(f"### {capitalized}")

            route_endpoints = endpoints.get(name, [])
            if not route_endpoints:
                # Default CRUD endpoints
                if name == "auth":
                    docs.append(f"- POST `/api/{name}/register` - Register new user")
                    docs.append(f"- POST `/api/{name}/login` - Login user")
                    docs.append(f"- POST `/api/{name}/logout` - Logout user")
                    docs.append(f"- GET `/api/{name}/me` - Get current user")
                else:
                    docs.append(f"- GET `/api/{name}` - List all {name}")
                    docs.append(f"- POST `/api/{name}` - Create {name}")
                    docs.append(f"- GET `/api/{name}/:id` - Get {name} by ID")
                    docs.append(f"- PUT `/api/{name}/:id` - Update {name}")
                    docs.append(f"- DELETE `/api/{name}/:id` - Delete {name}")
            else:
                for ep in route_endpoints:
                    if isinstance(ep, dict):
                        method = ep.get("method", "GET")
                        path = ep.get("path", "/")
                        desc = ep.get("description", "")
                        full_path = f"/api/{name}{path}" if not path.startswith("/api") else path
                        docs.append(f"- {method} `{full_path}` - {desc}")

            docs.append("")

        return "\n".join(docs)

    def _create_fastapi_backend(self, architecture: Dict, db_name: str) -> Dict[str, bool]:
        """Create Python/FastAPI backend with all files."""
        results = {}
        from rich.console import Console
        console = Console()

        # Create folders
        folders = [
            "backend/app/routers",
            "backend/app/models",
            "backend/app/schemas",
            "backend/app/services",
            "backend/app/config",
            "backend/app/utils"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created backend folders[/#F1F5F9] ✓")

        # Detect database package
        if "supabase" in db_name or "postgres" in db_name:
            db_package = "psycopg2-binary==2.9.9\nsqlalchemy==2.0.23"
        elif "mongo" in db_name:
            db_package = "pymongo==4.6.0"
        elif "mysql" in db_name:
            db_package = "mysql-connector-python==8.2.0\nsqlalchemy==2.0.23"
        else:
            db_package = "psycopg2-binary==2.9.9\nsqlalchemy==2.0.23"

        # requirements.txt
        requirements = f"""fastapi==0.108.0
uvicorn[standard]==0.25.0
python-dotenv==1.0.0
pydantic==2.5.3
{db_package}
bcrypt==4.1.2
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
"""
        results["backend/requirements.txt"] = self._write_file("backend/requirements.txt", requirements)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/requirements.txt ✓")

        # main.py
        main_py = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import routers
from app.routers import auth

load_dotenv()

app = FastAPI(title="Backend API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
        results["backend/main.py"] = self._write_file("backend/main.py", main_py)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/main.py ✓")

        # .env.example
        env_example = self._generate_backend_env_example(db_name)
        results["backend/.env.example"] = self._write_file("backend/.env.example", env_example)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/.env.example ✓")

        # .gitignore
        gitignore = """__pycache__/
*.py[cod]
*$py.class
.env
*.log
.DS_Store
venv/
.venv/
"""
        results["backend/.gitignore"] = self._write_file("backend/.gitignore", gitignore)

        # Router - auth.py
        auth_router = """from fastapi import APIRouter, HTTPException, Depends
from app.schemas.user import UserCreate, UserLogin, UserResponse
import bcrypt

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    try:
        # TODO: Check if user exists
        # TODO: Hash password
        # TODO: Create user in database

        return UserResponse(
            id="user_id",
            email=user.email,
            message="User registered successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(credentials: UserLogin):
    try:
        # TODO: Find user in database
        # TODO: Verify password
        # TODO: Generate JWT token

        return {
            "success": True,
            "token": "jwt_token_here",
            "user": {"email": credentials.email}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me")
async def get_me():
    # TODO: Get user from token
    return {"user": "current_user"}
"""
        results["backend/app/routers/auth.py"] = self._write_file("backend/app/routers/auth.py", auth_router)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/app/routers/auth.py ✓")

        # Schemas - user.py
        user_schemas = """from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    message: Optional[str] = None
"""
        results["backend/app/schemas/user.py"] = self._write_file("backend/app/schemas/user.py", user_schemas)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/app/schemas/user.py ✓")

        # __init__.py files
        results["backend/app/__init__.py"] = self._write_file("backend/app/__init__.py", "")
        results["backend/app/routers/__init__.py"] = self._write_file("backend/app/routers/__init__.py", "")
        results["backend/app/schemas/__init__.py"] = self._write_file("backend/app/schemas/__init__.py", "")

        # README.md
        readme = """# Backend API

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy .env.example to .env and fill in your credentials:
```bash
cp .env.example .env
```

4. Run development server:
```bash
python main.py
```

Server will start at http://localhost:8000

## API Endpoints

See `backend.md` for detailed backend setup instructions.
"""
        results["backend/README.md"] = self._write_file("backend/README.md", readme)

        return results

    def _create_django_backend(self, architecture: Dict, db_name: str) -> Dict[str, bool]:
        """Create Django backend with all files."""
        results = {}
        from rich.console import Console
        console = Console()

        # Create folders
        folders = [
            "backend/app",
            "backend/app/migrations",
            "backend/accounts",
            "backend/api"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created backend folders[/#F1F5F9] ✓")

        # requirements.txt
        db_package = ""
        if "postgres" in db_name or "supabase" in db_name:
            db_package = "psycopg2-binary==2.9.9"
        elif "mysql" in db_name:
            db_package = "mysqlclient==2.2.0"
        elif "mongo" in db_name:
            db_package = "djongo==1.3.6\npymongo==3.12.3"
        else:
            db_package = "psycopg2-binary==2.9.9"

        requirements = f"""Django==5.0.0
djangorestframework==3.14.0
django-cors-headers==4.3.1
python-dotenv==1.0.0
{db_package}
djangorestframework-simplejwt==5.3.1
"""
        results["backend/requirements.txt"] = self._write_file("backend/requirements.txt", requirements)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] backend/requirements.txt ✓")

        # manage.py
        manage_py = """#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)
"""
        results["backend/manage.py"] = self._write_file("backend/manage.py", manage_py)

        # settings.py (simplified)
        settings_py = """import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'
WSGI_APPLICATION = 'app.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'myapp_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

CORS_ALLOW_ALL_ORIGINS = True

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': ['django.template.context_processors.debug']},
}]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
"""
        results["backend/app/settings.py"] = self._write_file("backend/app/settings.py", settings_py)

        # urls.py
        urls_py = """from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
"""
        results["backend/app/urls.py"] = self._write_file("backend/app/urls.py", urls_py)

        # __init__.py files
        results["backend/app/__init__.py"] = self._write_file("backend/app/__init__.py", "")
        results["backend/api/__init__.py"] = self._write_file("backend/api/__init__.py", "")

        # .env.example
        env_example = self._generate_backend_env_example(db_name) + "\nSECRET_KEY=django-secret-key-change-this\nDEBUG=True\n"
        results["backend/.env.example"] = self._write_file("backend/.env.example", env_example)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created backend files[/#F1F5F9] ✓")

        return results

    def _create_flask_backend(self, architecture: Dict, db_name: str) -> Dict[str, bool]:
        """Create Flask backend with all files."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = ["backend/app/routes", "backend/app/models", "backend/app/utils"]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        db_package = ""
        if "postgres" in db_name or "supabase" in db_name:
            db_package = "psycopg2-binary==2.9.9"
        elif "mysql" in db_name:
            db_package = "mysql-connector-python==8.2.0"
        elif "mongo" in db_name:
            db_package = "pymongo==4.6.0"
        else:
            db_package = "psycopg2-binary==2.9.9"

        requirements = f"""Flask==3.0.0
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.1.1
python-dotenv==1.0.0
{db_package}
PyJWT==2.8.0
bcrypt==4.1.2
"""
        results["backend/requirements.txt"] = self._write_file("backend/requirements.txt", requirements)

        # app.py
        app_py = """from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-this-secret-key')
CORS(app)

from app.routes import auth

app.register_blueprint(auth.bp, url_prefix='/api/auth')

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
"""
        results["backend/app.py"] = self._write_file("backend/app.py", app_py)

        # routes/auth.py
        auth_route = """from flask import Blueprint, request, jsonify
import bcrypt
import jwt
import os

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    # TODO: Check if user exists
    # TODO: Hash password and create user
    return jsonify({'success': True, 'message': 'User registered'}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    # TODO: Verify credentials
    token = jwt.encode({'user_id': 'user_id_here'}, os.getenv('SECRET_KEY'), algorithm='HS256')
    return jsonify({'success': True, 'token': token})

@bp.route('/me', methods=['GET'])
def get_me():
    # TODO: Verify token and get user
    return jsonify({'user': 'current_user'})
"""
        results["backend/app/routes/auth.py"] = self._write_file("backend/app/routes/auth.py", auth_route)
        results["backend/app/__init__.py"] = self._write_file("backend/app/__init__.py", "")
        results["backend/app/routes/__init__.py"] = self._write_file("backend/app/routes/__init__.py", "")

        env_example = self._generate_backend_env_example(db_name) + "\nSECRET_KEY=flask-secret-key-change-this\n"
        results["backend/.env.example"] = self._write_file("backend/.env.example", env_example)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Flask backend[/#F1F5F9] ✓")

        return results

    def _create_go_backend(self, architecture: Dict, db_name: str) -> Dict[str, bool]:
        """Create Go/Gin backend with all files."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = ["backend/controllers", "backend/models", "backend/middleware", "backend/routes"]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        # go.mod
        go_mod = """module myapp

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/gin-contrib/cors v1.5.0
    github.com/joho/godotenv v1.5.1
    github.com/golang-jwt/jwt/v5 v5.2.0
    golang.org/x/crypto v0.17.0
)
"""
        results["backend/go.mod"] = self._write_file("backend/go.mod", go_mod)

        # main.go
        main_go = """package main

import (
    "log"
    "os"
    "github.com/gin-gonic/gin"
    "github.com/gin-contrib/cors"
    "github.com/joho/godotenv"
)

func main() {
    godotenv.Load()

    r := gin.Default()
    r.Use(cors.Default())

    api := r.Group("/api")
    {
        auth := api.Group("/auth")
        {
            auth.POST("/register", registerHandler)
            auth.POST("/login", loginHandler)
            auth.GET("/me", authMiddleware(), getMeHandler)
        }
    }

    r.GET("/health", func(c *gin.Context) {
        c.JSON(200, gin.H{"status": "healthy"})
    })

    port := os.Getenv("PORT")
    if port == "" {
        port = "8000"
    }

    log.Printf("Server running on :%s", port)
    r.Run(":" + port)
}

func registerHandler(c *gin.Context) {
    // TODO: Implement register
    c.JSON(201, gin.H{"success": true, "message": "User registered"})
}

func loginHandler(c *gin.Context) {
    // TODO: Implement login
    c.JSON(200, gin.H{"success": true, "token": "jwt_token_here"})
}

func getMeHandler(c *gin.Context) {
    // TODO: Get user from context
    c.JSON(200, gin.H{"user": "current_user"})
}

func authMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        // TODO: Verify JWT token
        c.Next()
    }
}
"""
        results["backend/main.go"] = self._write_file("backend/main.go", main_go)

        env_example = self._generate_backend_env_example(db_name) + "\nJWT_SECRET=go-jwt-secret-change-this\n"
        results["backend/.env.example"] = self._write_file("backend/.env.example", env_example)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Go/Gin backend[/#F1F5F9] ✓")

        return results

    def _create_rails_backend(self, architecture: Dict, db_name: str) -> Dict[str, bool]:
        """Create Ruby on Rails backend (API only)."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = ["backend/app/controllers", "backend/app/models", "backend/config"]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        # Gemfile
        gemfile = """source 'https://rubygems.org'

ruby '~> 3.2.0'

gem 'rails', '~> 7.1.0'
gem 'pg'
gem 'puma'
gem 'rack-cors'
gem 'bcrypt'
gem 'jwt'
gem 'dotenv-rails'

group :development, :test do
  gem 'debug'
end
"""
        results["backend/Gemfile"] = self._write_file("backend/Gemfile", gemfile)

        # config/application.rb
        application_rb = """require_relative "boot"
require "rails/all"

Bundler.require(*Rails.groups)

module Backend
  class Application < Rails::Application
    config.load_defaults 7.1
    config.api_only = true

    config.middleware.insert_before 0, Rack::Cors do
      allow do
        origins '*'
        resource '*', headers: :any, methods: [:get, :post, :put, :patch, :delete, :options]
      end
    end
  end
end
"""
        results["backend/config/application.rb"] = self._write_file("backend/config/application.rb", application_rb)

        # config/routes.rb
        routes_rb = """Rails.application.routes.draw do
  get "health", to: "health#index"

  namespace :api do
    post "auth/register", to: "auth#register"
    post "auth/login", to: "auth#login"
    get "auth/me", to: "auth#me"
  end
end
"""
        results["backend/config/routes.rb"] = self._write_file("backend/config/routes.rb", routes_rb)

        # app/controllers/api/auth_controller.rb
        auth_controller = """class Api::AuthController < ApplicationController
  def register
    # TODO: Create user
    render json: { success: true, message: 'User registered' }, status: :created
  end

  def login
    # TODO: Verify credentials and generate JWT
    render json: { success: true, token: 'jwt_token_here' }
  end

  def me
    # TODO: Get current user from token
    render json: { user: 'current_user' }
  end
end
"""
        results["backend/app/controllers/api/auth_controller.rb"] = self._write_file("backend/app/controllers/api/auth_controller.rb", auth_controller)

        env_example = self._generate_backend_env_example(db_name) + "\nSECRET_KEY_BASE=rails-secret-key-change-this\n"
        results["backend/.env.example"] = self._write_file("backend/.env.example", env_example)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Rails backend[/#F1F5F9] ✓")

        return results

    def _create_spring_backend(self, architecture: Dict, db_name: str) -> Dict[str, bool]:
        """Create Java Spring Boot backend."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = [
            "backend/src/main/java/com/myapp/controller",
            "backend/src/main/java/com/myapp/model",
            "backend/src/main/java/com/myapp/service",
            "backend/src/main/java/com/myapp/config",
            "backend/src/main/resources"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        # pom.xml
        pom_xml = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>
    <groupId>com.myapp</groupId>
    <artifactId>backend</artifactId>
    <version>1.0.0</version>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId>
            <version>0.12.3</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
"""
        results["backend/pom.xml"] = self._write_file("backend/pom.xml", pom_xml)

        # Application.java
        application_java = """package com.myapp;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
"""
        results["backend/src/main/java/com/myapp/Application.java"] = self._write_file("backend/src/main/java/com/myapp/Application.java", application_java)

        # AuthController.java
        auth_controller_java = """package com.myapp.controller;

import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @PostMapping("/register")
    public Object register(@RequestBody Object user) {
        // TODO: Implement registration
        return Map.of("success", true, "message", "User registered");
    }

    @PostMapping("/login")
    public Object login(@RequestBody Object credentials) {
        // TODO: Implement login
        return Map.of("success", true, "token", "jwt_token_here");
    }

    @GetMapping("/me")
    public Object getMe() {
        // TODO: Get current user
        return Map.of("user", "current_user");
    }
}
"""
        results["backend/src/main/java/com/myapp/controller/AuthController.java"] = self._write_file("backend/src/main/java/com/myapp/controller/AuthController.java", auth_controller_java)

        # application.properties
        app_properties = """server.port=8000
spring.datasource.url=jdbc:postgresql://localhost:5432/myapp_db
spring.datasource.username=postgres
spring.datasource.password=
spring.jpa.hibernate.ddl-auto=update
"""
        results["backend/src/main/resources/application.properties"] = self._write_file("backend/src/main/resources/application.properties", app_properties)

        env_example = self._generate_backend_env_example(db_name) + "\nJWT_SECRET=spring-jwt-secret-change-this\n"
        results["backend/.env.example"] = self._write_file("backend/.env.example", env_example)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Spring Boot backend[/#F1F5F9] ✓")

        return results

    def _create_laravel_backend(self, architecture: Dict, db_name: str) -> Dict[str, bool]:
        """Create PHP Laravel backend."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = [
            "backend/app/Http/Controllers",
            "backend/app/Models",
            "backend/routes",
            "backend/config"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        # composer.json
        composer_json = """{
    "name": "myapp/backend",
    "type": "project",
    "require": {
        "php": "^8.2",
        "laravel/framework": "^11.0",
        "tymon/jwt-auth": "^2.0"
    },
    "autoload": {
        "psr-4": {
            "App\\\\": "app/"
        }
    }
}
"""
        results["backend/composer.json"] = self._write_file("backend/composer.json", composer_json)

        # routes/api.php
        api_routes = """<?php

use Illuminate\\Support\\Facades\\Route;
use App\\Http\\Controllers\\AuthController;

Route::post('/auth/register', [AuthController::class, 'register']);
Route::post('/auth/login', [AuthController::class, 'login']);
Route::get('/auth/me', [AuthController::class, 'me'])->middleware('auth:api');
Route::get('/health', function() { return response()->json(['status' => 'healthy']); });
"""
        results["backend/routes/api.php"] = self._write_file("backend/routes/api.php", api_routes)

        # AuthController.php
        auth_controller_php = """<?php

namespace App\\Http\\Controllers;

use Illuminate\\Http\\Request;

class AuthController extends Controller
{
    public function register(Request $request)
    {
        // TODO: Validate and create user
        return response()->json(['success' => true, 'message' => 'User registered'], 201);
    }

    public function login(Request $request)
    {
        // TODO: Verify credentials and generate JWT
        return response()->json(['success' => true, 'token' => 'jwt_token_here']);
    }

    public function me()
    {
        // TODO: Get authenticated user
        return response()->json(['user' => 'current_user']);
    }
}
"""
        results["backend/app/Http/Controllers/AuthController.php"] = self._write_file("backend/app/Http/Controllers/AuthController.php", auth_controller_php)

        # .env.example
        env_example = self._generate_backend_env_example(db_name) + "\nAPP_KEY=\nJWT_SECRET=laravel-jwt-secret-change-this\n"
        results["backend/.env.example"] = self._write_file("backend/.env.example", env_example)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Laravel backend[/#F1F5F9] ✓")

        return results

    def _create_dotnet_backend(self, architecture: Dict, db_name: str) -> Dict[str, bool]:
        """Create .NET/ASP.NET Core backend."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = [
            "backend/Controllers",
            "backend/Models",
            "backend/Services"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        # backend.csproj
        csproj = """<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.0" />
    <PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" Version="8.0.0" />
    <PackageReference Include="Microsoft.AspNetCore.Authentication.JwtBearer" Version="8.0.0" />
    <PackageReference Include="BCrypt.Net-Next" Version="4.0.3" />
  </ItemGroup>
</Project>
"""
        results["backend/backend.csproj"] = self._write_file("backend/backend.csproj", csproj)

        # Program.cs
        program_cs = """using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader();
    });
});

var app = builder.Build();

app.UseCors();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

app.MapGet("/health", () => new { status = "healthy" });

app.Run("http://localhost:8000");
"""
        results["backend/Program.cs"] = self._write_file("backend/Program.cs", program_cs)

        # Controllers/AuthController.cs
        auth_controller_cs = """using Microsoft.AspNetCore.Mvc;

namespace Backend.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    [HttpPost("register")]
    public IActionResult Register([FromBody] object user)
    {
        // TODO: Implement registration
        return CreatedAtAction(nameof(Register), new { success = true, message = "User registered" });
    }

    [HttpPost("login")]
    public IActionResult Login([FromBody] object credentials)
    {
        // TODO: Implement login
        return Ok(new { success = true, token = "jwt_token_here" });
    }

    [HttpGet("me")]
    public IActionResult GetMe()
    {
        // TODO: Get current user
        return Ok(new { user = "current_user" });
    }
}
"""
        results["backend/Controllers/AuthController.cs"] = self._write_file("backend/Controllers/AuthController.cs", auth_controller_cs)

        # appsettings.json
        appsettings = """{
  "ConnectionStrings": {
    "DefaultConnection": "Host=localhost;Database=myapp_db;Username=postgres;Password="
  },
  "Jwt": {
    "Secret": "your-jwt-secret-key-change-this",
    "Issuer": "myapp",
    "Audience": "myapp"
  }
}
"""
        results["backend/appsettings.json"] = self._write_file("backend/appsettings.json", appsettings)

        env_example = self._generate_backend_env_example(db_name) + "\nJWT_SECRET=dotnet-jwt-secret-change-this\n"
        results["backend/.env.example"] = self._write_file("backend/.env.example", env_example)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created .NET backend[/#F1F5F9] ✓")

        return results

    def _generate_backend_env_example(self, db_name: str) -> str:
        """Generate .env.example for backend based on database type."""
        env_content = "# Database Configuration\n"

        if "supabase" in db_name:
            env_content += """SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
"""
        elif "mongo" in db_name:
            env_content += """MONGODB_URI=mongodb://localhost:27017
DB_NAME=myapp_db
"""
        elif "postgres" in db_name:
            env_content += """DATABASE_URL=postgresql://username:password@localhost:5432/myapp_db
"""
        elif "mysql" in db_name:
            env_content += """DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=myapp_db
"""
        else:
            env_content += """DATABASE_URL=postgresql://username:password@localhost:5432/myapp_db
"""

        env_content += """
# Server Configuration
PORT=8000
NODE_ENV=development

# JWT Secret (generate a random string)
JWT_SECRET=your_super_secret_jwt_key_change_this_in_production
"""

        return env_content

    def _generate_backend_md(self, backend_name: str, db_name: str, architecture: Dict) -> str:
        """Generate comprehensive backend.md documentation."""

        content = f"""# Backend Setup Guide

## Overview

This backend is built with **{backend_name}** and connects to **{db_name}**.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Database Connection](#database-connection)
4. [Environment Variables](#environment-variables)
5. [Running the Server](#running-the-server)
6. [API Endpoints](#api-endpoints)
7. [Project Structure](#project-structure)
8. [Adding New Features](#adding-new-features)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

"""

        if "node" in backend_name or "express" in backend_name:
            content += """- Node.js 18+ installed
- npm or yarn package manager
"""
        else:
            content += """- Python 3.9+ installed
- pip package manager
- Virtual environment (recommended)
"""

        content += f"""- {db_name} database installed and running (see database/README.md)

---

## Installation

"""

        if "node" in backend_name or "express" in backend_name:
            content += """### Step 1: Install Dependencies

```bash
cd backend
npm install
```

This will install all required packages:
- Express (web framework)
- CORS (cross-origin requests)
- dotenv (environment variables)
- Database client (based on your database)
- bcrypt (password hashing)
- jsonwebtoken (JWT authentication)
"""
        else:
            content += """### Step 1: Create Virtual Environment

```bash
cd backend
python -m venv venv
```

### Step 2: Activate Virtual Environment

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\\Scripts\\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- Database client (based on your database)
- bcrypt (password hashing)
- python-jose (JWT authentication)
"""

        content += """
---

## Database Connection

The database connection is already configured in `src/config/database.js` (or `app/config/database.py`).

"""

        if "supabase" in db_name:
            content += """### Supabase Connection

Your backend connects to Supabase using the credentials in `.env`:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
)
```

**Get your credentials:**
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to Settings → API
4. Copy URL and service_role key
"""
        elif "mongo" in db_name:
            content += """### MongoDB Connection

Your backend connects to MongoDB using:

```javascript
import { MongoClient } from 'mongodb'

const client = new MongoClient(process.env.MONGODB_URI)
await client.connect()
const db = client.db(process.env.DB_NAME)
```

**For local MongoDB:**
- URI: `mongodb://localhost:27017`
- DB Name: Your app name

**For MongoDB Atlas (cloud):**
- Get connection string from https://cloud.mongodb.com
- Replace `<password>` with your actual password
"""
        elif "postgres" in db_name:
            content += """### PostgreSQL Connection

Your backend connects to PostgreSQL using:

```javascript
import pg from 'pg'
const { Pool } = pg

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
})
```

**Connection string format:**
```
postgresql://username:password@localhost:5432/database_name
```

**Test connection:**
```bash
psql -d myapp_db -U username
```
"""
        elif "mysql" in db_name:
            content += """### MySQL Connection

Your backend connects to MySQL using:

```javascript
import mysql from 'mysql2/promise'

const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME
})
```

**Test connection:**
```bash
mysql -u root -p myapp_db
```
"""

        content += """
---

## Environment Variables

### Step 1: Copy .env.example

```bash
cp .env.example .env
```

### Step 2: Fill in Your Credentials

Open `.env` and add your actual values:

"""

        if "supabase" in db_name:
            content += """```
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...your_key
SUPABASE_SERVICE_KEY=eyJhbGc...your_service_key

PORT=8000
JWT_SECRET=your_random_secret_string_here
```

**Where to get these:**
- Supabase Dashboard → Settings → API
- Copy Project URL
- Copy anon (public) key
- Copy service_role key (keep this secret!)
"""
        elif "mongo" in db_name:
            content += """```
MONGODB_URI=mongodb://localhost:27017
DB_NAME=myapp_db

PORT=8000
JWT_SECRET=your_random_secret_string_here
```

**For MongoDB Atlas:**
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
```
"""
        else:
            content += """```
DATABASE_URL=postgresql://username:password@localhost:5432/myapp_db

PORT=8000
JWT_SECRET=your_random_secret_string_here
```
"""

        content += """
**IMPORTANT:** Never commit `.env` to git! It's in `.gitignore`.

---

## Running the Server

"""

        if "node" in backend_name or "express" in backend_name:
            content += """### Development Mode (with auto-reload)

```bash
npm run dev
```

### Production Mode

```bash
npm start
```

You should see:
```
✓ Server running on http://localhost:8000
```

### Test the Server

Open browser or use curl:
```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status":"healthy","timestamp":"2024-01-15T10:30:00.000Z"}
```
"""
        else:
            content += """### Development Mode

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test the Server

Open browser or use curl:
```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status":"healthy"}
```

### Interactive API Docs

FastAPI provides automatic interactive docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
"""

        # Add API endpoints section
        endpoints = architecture.get("endpoints", [])

        content += """
---

## API Endpoints

### Authentication

"""

        if endpoints:
            for endpoint in endpoints:
                if isinstance(endpoint, dict):
                method = endpoint.get("method", "GET")
                path = endpoint.get("path", "")
                description = endpoint.get("description", "")
                content += f"- **{method}** `{path}` - {description}\n"
                else:
                    content += f"- {endpoint}\n"
        else:
            content += """- **POST** `/api/auth/register` - Register new user
- **POST** `/api/auth/login` - Login user
- **POST** `/api/auth/logout` - Logout user
- **GET** `/api/auth/me` - Get current user info

### Health Check

- **GET** `/health` - Check if server is running
"""

        content += """
### Example API Calls

**Register User:**
```bash
curl -X POST http://localhost:8000/api/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "name": "John Doe"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "email": "user@example.com"
  }
}
```

**Get Current User (requires token):**
```bash
curl http://localhost:8000/api/auth/me \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Project Structure

"""

        if "node" in backend_name or "express" in backend_name:
            content += """```
backend/
├── src/
│   ├── routes/          # API route definitions
│   │   └── auth.js      # Authentication routes
│   ├── controllers/     # Business logic for routes
│   │   └── authController.js
│   ├── services/        # Reusable business logic
│   ├── middleware/      # Express middleware
│   │   └── auth.js      # JWT authentication middleware
│   ├── config/          # Configuration files
│   │   └── database.js  # Database connection
│   └── utils/           # Utility functions
├── server.js            # Main entry point
├── package.json         # Dependencies
├── .env                 # Environment variables (DO NOT COMMIT)
├── .env.example         # Example environment variables
└── README.md
```

### How It Works

1. **server.js** - Sets up Express app, middleware, routes
2. **routes/** - Define API endpoints
3. **controllers/** - Handle request/response logic
4. **middleware/** - Authenticate requests, handle errors
5. **config/database.js** - Database connection (already configured!)
"""
        else:
            content += """```
backend/
├── app/
│   ├── routers/         # API route definitions
│   │   └── auth.py      # Authentication routes
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas (request/response validation)
│   │   └── user.py
│   ├── services/        # Business logic
│   ├── config/          # Configuration files
│   │   └── database.py  # Database connection
│   └── utils/           # Utility functions
├── main.py              # Main entry point
├── requirements.txt     # Dependencies
├── .env                 # Environment variables (DO NOT COMMIT)
├── .env.example         # Example environment variables
└── README.md
```

### How It Works

1. **main.py** - Creates FastAPI app, includes routers
2. **routers/** - Define API endpoints
3. **schemas/** - Validate request/response data
4. **config/database.py** - Database connection (already configured!)
"""

        content += """
---

## Adding New Features

### Step 1: Create Route
"""

        if "node" in backend_name or "express" in backend_name:
            content += """
Create new file in `src/routes/` (e.g., `posts.js`):

```javascript
import express from 'express'
import { getPosts, createPost } from '../controllers/postsController.js'
import { authenticate } from '../middleware/auth.js'

const router = express.Router()

router.get('/', getPosts)
router.post('/', authenticate, createPost)

export default router
```

### Step 2: Create Controller

Create `src/controllers/postsController.js`:

```javascript
export const getPosts = async (req, res) => {
  try {
    // TODO: Fetch posts from database
    res.json({ posts: [] })
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
}

export const createPost = async (req, res) => {
  try {
    const { title, content } = req.body
    // TODO: Create post in database
    res.status(201).json({ success: true })
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
}
```

### Step 3: Register Route in server.js

```javascript
import postsRoutes from './src/routes/posts.js'

app.use('/api/posts', postsRoutes)
```
"""
        else:
            content += """
Create new file in `app/routers/` (e.g., `posts.py`):

```python
from fastapi import APIRouter, Depends
from app.schemas.post import PostCreate, PostResponse

router = APIRouter()

@router.get("/")
async def get_posts():
    # TODO: Fetch posts from database
    return {"posts": []}

@router.post("/", response_model=PostResponse)
async def create_post(post: PostCreate):
    # TODO: Create post in database
    return PostResponse(id="1", title=post.title)
```

### Step 2: Create Schema

Create `app/schemas/post.py`:

```python
from pydantic import BaseModel

class PostCreate(BaseModel):
    title: str
    content: str

class PostResponse(BaseModel):
    id: str
    title: str
```

### Step 3: Register Router in main.py

```python
from app.routers import posts

app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
```
"""

        content += """
---

## Troubleshooting

### Server Won't Start

"""

        if "node" in backend_name or "express" in backend_name:
            content += """**Check if port 8000 is in use:**
```bash
lsof -i :8000
# Kill the process if needed
kill -9 <PID>
```

**Check Node.js version:**
```bash
node --version  # Should be 18+
```

**Reinstall dependencies:**
```bash
rm -rf node_modules package-lock.json
npm install
```
"""
        else:
            content += """**Check if port 8000 is in use:**
```bash
lsof -i :8000
# Kill the process if needed
kill -9 <PID>
```

**Check Python version:**
```bash
python --version  # Should be 3.9+
```

**Reinstall dependencies:**
```bash
pip install -r requirements.txt --force-reinstall
```
"""

        content += """
### Database Connection Fails

1. **Check database is running:**
"""

        if "supabase" in db_name:
            content += """   - Go to Supabase dashboard
   - Check project status
   - Verify credentials in .env
"""
        elif "mongo" in db_name:
            content += """   ```bash
   # Check if MongoDB is running
   mongo --eval "db.stats()"
   ```
"""
        elif "postgres" in db_name:
            content += """   ```bash
   # Check if PostgreSQL is running
   psql -U postgres -c "SELECT 1"
   ```
"""
        elif "mysql" in db_name:
            content += """   ```bash
   # Check if MySQL is running
   mysql -u root -p -e "SELECT 1"
   ```
"""

        content += """
2. **Verify .env credentials:**
   - Double-check DATABASE_URL or connection details
   - Make sure no extra spaces
   - Test connection manually

3. **Check database exists:**
   - Run migrations from database/README.md
   - Ensure all tables are created

### JWT Token Errors

- Make sure `JWT_SECRET` is set in `.env`
- Use a long random string (at least 32 characters)
- Never use the same secret in production as development

### CORS Errors

If frontend can't connect:
- Check CORS settings in server file
- Make sure frontend URL is in allowed origins
- For development, `"*"` allows all origins

---

## Production Deployment

See deployment guide for deploying to:
- Railway
- Heroku
- DigitalOcean
- AWS
- Vercel (for Node.js backends)

---

## Need Help?

- Check `database/README.md` for database setup
- See API documentation at http://localhost:8000/docs (FastAPI)
- Review error logs in console

Your backend is ready! Start building your API endpoints. 🚀
"""

        return content

    def create_frontend_files(self) -> Dict[str, bool]:
        """
        Create complete frontend structure with all files (100%).

        Returns:
            Dict of file paths to success status
        """
        results = {}

        # Load project data (try multiple sources)
        project = self.storage.load("project") or {}
        tech_stack = self.storage.load("tech_stack") or project.get("tech_stack", {})
        frontend_info = tech_stack.get("frontend", {})
        frontend_design = self.storage.load("frontend_design") or {}
        backend_arch = self.storage.load("backend_design") or {}

        frontend_name = frontend_info.get("name", "react").lower() if isinstance(frontend_info, dict) else str(frontend_info).lower()

        from rich.console import Console
        console = Console()
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Creating frontend:[/#F1F5F9] {frontend_name}")

        # Detect frontend type
        if "react" in frontend_name and "native" not in frontend_name and "next" not in frontend_name:
            results.update(self._create_react_vite_frontend(frontend_design))
        elif "next" in frontend_name or "nextjs" in frontend_name:
            results.update(self._create_nextjs_frontend(frontend_design))
        elif "vue" in frontend_name:
            results.update(self._create_vuejs_frontend(frontend_design))
        elif "angular" in frontend_name:
            results.update(self._create_angular_frontend(frontend_design))
        elif "svelte" in frontend_name:
            results.update(self._create_svelte_frontend(frontend_design))
        elif "react native" in frontend_name or "react-native" in frontend_name:
            results.update(self._create_react_native_frontend(frontend_design))
        elif "flutter" in frontend_name:
            results.update(self._create_flutter_frontend(frontend_design))
        elif "swift" in frontend_name or "ios" in frontend_name:
            results.update(self._create_swift_frontend(frontend_design))
        elif "kotlin" in frontend_name or "android" in frontend_name:
            results.update(self._create_kotlin_frontend(frontend_design))
        elif "electron" in frontend_name:
            results.update(self._create_electron_frontend(frontend_design))
        else:
            # Default to React/Vite
            results.update(self._create_react_vite_frontend(frontend_design))

        # Create frontend.md documentation (method writes file itself and returns bool)
        frontend_md_success = self._generate_frontend_md(project, frontend_design, backend_arch)
        results["frontend/frontend.md"] = frontend_md_success
        if frontend_md_success:
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] frontend/frontend.md ✓")

        return results

    def _create_react_vite_frontend(self, design: Dict) -> Dict[str, bool]:
        """Create React with Vite frontend DYNAMICALLY from design."""
        results = {}
        from rich.console import Console
        console = Console()

        # Get pages and components from design (dynamic!)
        pages = design.get("pages", ["Login", "Home"])
        components = design.get("components", [])

        # Normalize page names - filter out generic/platform names
        GENERIC_NAMES = {"web", "mobile", "ios", "android", "page", "component", "view", "screen"}
        page_names = []
        for page in pages:
            if isinstance(page, dict):
                name = page.get("name", "Page")
            else:
                name = str(page)
            # Skip generic names
            if name and name.lower() not in GENERIC_NAMES and name not in page_names:
                page_names.append(name)

        # Ensure essential pages
        if "Login" not in page_names:
            page_names.insert(0, "Login")
        if "Register" not in page_names:
            page_names.insert(1, "Register")
        if "Dashboard" not in page_names and "Home" not in page_names:
            page_names.append("Dashboard")

        # Normalize component names - filter out generic names
        GENERIC_COMPONENT_NAMES = {"component", "reusable", "layouts", "features", "ui", "element"}
        component_names = []
        for comp in components:
            if isinstance(comp, dict):
                name = comp.get("name", "Component")
            else:
                name = str(comp)
            # Skip generic names
            if name and name.lower() not in GENERIC_COMPONENT_NAMES and name not in component_names:
                component_names.append(name)

        folders = [
            "frontend/src/components/ui",
            "frontend/src/components/layout",
            "frontend/src/components/features",
            "frontend/src/pages",
            "frontend/src/services",
            "frontend/src/hooks",
            "frontend/src/context",
            "frontend/src/utils",
            "frontend/public"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created frontend folders[/#F1F5F9] ✓")

        # package.json
        package_json = """{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}"""
        results["frontend/package.json"] = self._write_file("frontend/package.json", package_json)

        # vite.config.js
        vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000
  }
})"""
        results["frontend/vite.config.js"] = self._write_file("frontend/vite.config.js", vite_config)

        # tailwind.config.js
        tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}"""
        results["frontend/tailwind.config.js"] = self._write_file("frontend/tailwind.config.js", tailwind_config)

        # postcss.config.js
        postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}"""
        results["frontend/postcss.config.js"] = self._write_file("frontend/postcss.config.js", postcss_config)

        # index.html
        index_html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>"""
        results["frontend/index.html"] = self._write_file("frontend/index.html", index_html)

        # src/main.jsx
        main_jsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)"""
        results["frontend/src/main.jsx"] = self._write_file("frontend/src/main.jsx", main_jsx)

        # Generate dynamic App.jsx with all pages
        page_imports = "\n".join([f"import {name} from './pages/{name}'" for name in page_names])
        page_routes = []
        for name in page_names:
            route_path = self._page_name_to_route(name)
            page_routes.append(f'        <Route path="{route_path}" element={{<{name} />}} />')
        routes_jsx = "\n".join(page_routes)

        app_jsx = f"""import {{ BrowserRouter, Routes, Route }} from 'react-router-dom'
{page_imports}

function App() {{
  return (
    <BrowserRouter>
      <Routes>
{routes_jsx}
      </Routes>
    </BrowserRouter>
  )
}}

export default App"""
        results["frontend/src/App.jsx"] = self._write_file("frontend/src/App.jsx", app_jsx)

        # src/index.css
        index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;"""
        results["frontend/src/index.css"] = self._write_file("frontend/src/index.css", index_css)

        # src/services/api.js
        api_js = """import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;"""
        results["frontend/src/services/api.js"] = self._write_file("frontend/src/services/api.js", api_js)

        # src/services/auth.js
        auth_js = """import api from './api';

export const authService = {
  async login(email, password) {
    const response = await api.post('/api/auth/login', { email, password });
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
    }
    return response.data;
  },

  async register(email, password, name) {
    const response = await api.post('/api/auth/register', { email, password, name });
    return response.data;
  },

  async logout() {
    localStorage.removeItem('token');
    await api.post('/api/auth/logout');
  },

  async getMe() {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  isAuthenticated() {
    return !!localStorage.getItem('token');
  }
};"""
        results["frontend/src/services/auth.js"] = self._write_file("frontend/src/services/auth.js", auth_js)

        # Create ALL pages dynamically
        for page_name in page_names:
            page_content = self._generate_react_page(page_name)
            results[f"frontend/src/pages/{page_name}.jsx"] = self._write_file(f"frontend/src/pages/{page_name}.jsx", page_content)
            console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] frontend/src/pages/{page_name}.jsx ✓")

        # Create ALL components dynamically
        for comp_name in component_names:
            comp_content = self._generate_react_component(comp_name)
            # Determine folder based on component type
            folder = "features"
            if comp_name.lower() in ["navbar", "header", "footer", "sidebar", "layout"]:
                folder = "layout"
            elif comp_name.lower() in ["button", "input", "card", "modal", "spinner", "loader"]:
                folder = "ui"
            results[f"frontend/src/components/{folder}/{comp_name}.jsx"] = self._write_file(f"frontend/src/components/{folder}/{comp_name}.jsx", comp_content)
            console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] frontend/src/components/{folder}/{comp_name}.jsx ✓")

        # .env.example
        env_example = """VITE_API_URL=http://localhost:8000"""
        results["frontend/.env.example"] = self._write_file("frontend/.env.example", env_example)

        # .gitignore
        gitignore = """node_modules
dist
.env
.env.local
*.log
.DS_Store"""
        results["frontend/.gitignore"] = self._write_file("frontend/.gitignore", gitignore)

        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created React/Vite frontend[/#F1F5F9] ✓")
        return results

    def _page_name_to_route(self, name: str) -> str:
        """Convert page name to route path."""
        name_lower = name.lower()
        if name_lower in ["home", "index", "main", "dashboard"]:
            return "/"
        elif name_lower == "login":
            return "/login"
        elif name_lower == "register":
            return "/register"
        else:
            # Convert CamelCase to kebab-case
            import re
            route = re.sub(r'(?<!^)(?=[A-Z])', '-', name).lower()
            return f"/{route}"

    def _generate_react_page(self, name: str) -> str:
        """Generate a React page component dynamically."""
        name_lower = name.lower()

        # Special pages with full implementations
        if name_lower == "login":
            return """import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authService } from '../services/auth'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await authService.login(email, password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-center mb-6">Login</h2>
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 disabled:bg-blue-300"
          >
            {loading ? 'Loading...' : 'Login'}
          </button>
        </form>
        <p className="text-center mt-4 text-sm text-gray-600">
          Don't have an account? <Link to="/register" className="text-blue-500 hover:underline">Register</Link>
        </p>
      </div>
    </div>
  )
}"""

        elif name_lower == "register":
            return """import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authService } from '../services/auth'

export default function Register() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await authService.register(email, password, name)
      navigate('/login')
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-center mb-6">Register</h2>
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 disabled:bg-blue-300"
          >
            {loading ? 'Loading...' : 'Register'}
          </button>
        </form>
        <p className="text-center mt-4 text-sm text-gray-600">
          Already have an account? <Link to="/login" className="text-blue-500 hover:underline">Login</Link>
        </p>
      </div>
    </div>
  )
}"""

        elif name_lower in ["home", "index", "main"]:
            return """import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/auth'

export default function Home() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login')
      return
    }

    authService.getMe()
      .then(data => setUser(data.user))
      .catch(() => navigate('/login'))
  }, [navigate])

  const handleLogout = async () => {
    await authService.logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold">My App</h1>
            </div>
            <div className="flex items-center">
              <button
                onClick={handleLogout}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h2 className="text-2xl font-bold mb-4">Welcome!</h2>
          {user && <p>Logged in as: {user.email}</p>}
        </div>
      </main>
    </div>
  )
}"""

        elif name_lower == "dashboard":
            return f"""import {{ useEffect, useState }} from 'react'
import {{ useNavigate }} from 'react-router-dom'
import {{ authService }} from '../services/auth'
import api from '../services/api'

export default function Dashboard() {{
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {{
    if (!authService.isAuthenticated()) {{
      navigate('/login')
      return
    }}

    const fetchData = async () => {{
      try {{
        const userRes = await authService.getMe()
        setUser(userRes.user)
        // TODO: Fetch dashboard data
        // const dataRes = await api.get('/api/dashboard')
        // setData(dataRes.data)
      }} catch (err) {{
        navigate('/login')
      }} finally {{
        setLoading(false)
      }}
    }}

    fetchData()
  }}, [navigate])

  const handleLogout = async () => {{
    await authService.logout()
    navigate('/login')
  }}

  if (loading) {{
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }}

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold">Dashboard</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-gray-600">{{user?.email}}</span>
              <button
                onClick={{handleLogout}}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900">Total Items</h3>
              <p className="text-3xl font-bold text-blue-600">0</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900">Active</h3>
              <p className="text-3xl font-bold text-green-600">0</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900">Pending</h3>
              <p className="text-3xl font-bold text-yellow-600">0</p>
            </div>
          </div>
          <div className="mt-8 bg-white rounded-lg shadow">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
              <p className="text-gray-500">No recent activity</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}}"""

        elif name_lower == "settings":
            return """import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/auth'
import api from '../services/api'

export default function Settings() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    notifications: true,
    darkMode: false
  })

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login')
      return
    }
    loadSettings()
  }, [navigate])

  const loadSettings = async () => {
    try {
      const res = await authService.getMe()
      setUser(res.user)
      setFormData({
        name: res.user.name || '',
        email: res.user.email || '',
        notifications: res.user.notifications ?? true,
        darkMode: res.user.darkMode ?? false
      })
    } catch (err) {
      navigate('/login')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    try {
      await api.put('/api/users/settings', formData)
      setMessage('Settings saved successfully!')
    } catch (err) {
      setMessage(err.response?.data?.error || 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold">Settings</h1>
            </div>
            <div className="flex items-center">
              <button onClick={() => navigate('/')} className="text-gray-600 hover:text-gray-900">
                ← Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-3xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold mb-6">Account Settings</h2>
          {message && (
            <div className={`mb-4 p-3 rounded ${message.includes('success') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              {message}
            </div>
          )}
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-gray-700 font-bold mb-2">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-gray-700 font-bold mb-2">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.notifications}
                  onChange={(e) => setFormData({...formData, notifications: e.target.checked})}
                  className="mr-2"
                />
                <span>Email Notifications</span>
              </label>
            </div>
            <div className="mb-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.darkMode}
                  onChange={(e) => setFormData({...formData, darkMode: e.target.checked})}
                  className="mr-2"
                />
                <span>Dark Mode</span>
              </label>
            </div>
            <button
              type="submit"
              disabled={saving}
              className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-blue-300"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        </div>
      </main>
    </div>
  )
}"""

        elif name_lower in ["forgotpassword", "forgot-password", "resetpassword", "reset-password"]:
            return """import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')
    setError('')

    try {
      await api.post('/api/auth/forgot-password', { email })
      setMessage('If an account exists with this email, you will receive a password reset link.')
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send reset email')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-center mb-6">Reset Password</h2>
        <p className="text-gray-600 text-center mb-6">
          Enter your email address and we'll send you a link to reset your password.
        </p>
        {message && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            {message}
          </div>
        )}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 disabled:bg-blue-300"
          >
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>
        <p className="text-center mt-4 text-sm text-gray-600">
          <Link to="/login" className="text-blue-500 hover:underline">Back to Login</Link>
        </p>
      </div>
    </div>
  )
}"""

        elif name_lower == "profile":
            return """import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/auth'
import api from '../services/api'

export default function Profile() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [formData, setFormData] = useState({ name: '', bio: '' })
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login')
      return
    }
    loadProfile()
  }, [navigate])

  const loadProfile = async () => {
    try {
      const res = await authService.getMe()
      setUser(res.user)
      setFormData({ name: res.user.name || '', bio: res.user.bio || '' })
    } catch (err) {
      navigate('/login')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      await api.put('/api/users/profile', formData)
      setUser({ ...user, ...formData })
      setEditing(false)
      setMessage('Profile updated!')
      setTimeout(() => setMessage(''), 3000)
    } catch (err) {
      setMessage(err.response?.data?.error || 'Failed to update')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold">Profile</h1>
            </div>
            <div className="flex items-center">
              <button onClick={() => navigate('/')} className="text-gray-600 hover:text-gray-900">
                ← Back
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-3xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow p-6">
          {message && (
            <div className="mb-4 p-3 bg-green-100 text-green-700 rounded">{message}</div>
          )}
          <div className="flex items-center mb-6">
            <div className="w-20 h-20 bg-blue-500 rounded-full flex items-center justify-center text-white text-2xl font-bold">
              {user?.name?.charAt(0) || user?.email?.charAt(0) || '?'}
            </div>
            <div className="ml-4">
              {editing ? (
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="text-xl font-bold border rounded px-2 py-1"
                />
              ) : (
                <h2 className="text-xl font-bold">{user?.name || 'User'}</h2>
              )}
              <p className="text-gray-600">{user?.email}</p>
            </div>
          </div>
          <div className="mb-4">
            <label className="block text-gray-700 font-bold mb-2">Bio</label>
            {editing ? (
              <textarea
                value={formData.bio}
                onChange={(e) => setFormData({...formData, bio: e.target.value})}
                className="w-full px-3 py-2 border rounded"
                rows="3"
              />
            ) : (
              <p className="text-gray-600">{user?.bio || 'No bio yet'}</p>
            )}
          </div>
          <div className="flex gap-2">
            {editing ? (
              <>
                <button onClick={handleSave} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                  Save
                </button>
                <button onClick={() => setEditing(false)} className="bg-gray-300 px-4 py-2 rounded hover:bg-gray-400">
                  Cancel
                </button>
              </>
            ) : (
              <button onClick={() => setEditing(true)} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                Edit Profile
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}"""

        elif name_lower == "editor":
            return """import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { authService } from '../services/auth'
import api from '../services/api'

export default function Editor() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [content, setContent] = useState('')
  const [title, setTitle] = useState('Untitled')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login')
      return
    }
    if (id) {
      loadDocument()
    } else {
      setLoading(false)
    }
  }, [navigate, id])

  const loadDocument = async () => {
    try {
      const res = await api.get(`/api/documents/${id}`)
      setTitle(res.data.title || 'Untitled')
      setContent(res.data.content || '')
    } catch (err) {
      console.error('Failed to load document')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      if (id) {
        await api.put(`/api/documents/${id}`, { title, content })
      } else {
        const res = await api.post('/api/documents', { title, content })
        navigate(`/editor/${res.data.id}`, { replace: true })
      }
      setLastSaved(new Date())
    } catch (err) {
      console.error('Failed to save')
    } finally {
      setSaving(false)
    }
  }

  // Auto-save every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (content) handleSave()
    }, 30000)
    return () => clearInterval(interval)
  }, [content])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-14">
            <div className="flex items-center gap-4">
              <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white">
                ← Back
              </button>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="bg-transparent border-none text-lg font-semibold focus:outline-none focus:ring-0"
              />
            </div>
            <div className="flex items-center gap-4">
              {lastSaved && (
                <span className="text-gray-400 text-sm">
                  Saved {lastSaved.toLocaleTimeString()}
                </span>
              )}
              <button
                onClick={handleSave}
                disabled={saving}
                className="bg-blue-600 text-white px-4 py-1.5 rounded hover:bg-blue-700 disabled:bg-blue-400"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-4xl mx-auto py-6 px-4">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Start writing..."
          className="w-full h-[calc(100vh-150px)] bg-transparent text-gray-100 text-lg leading-relaxed resize-none focus:outline-none font-mono"
        />
      </main>
    </div>
  )
}"""

        elif name_lower == "share":
            return """import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import api from '../services/api'

export default function Share() {
  const { id } = useParams()
  const [item, setItem] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    loadSharedItem()
  }, [id])

  const loadSharedItem = async () => {
    try {
      const res = await api.get(`/api/share/${id}`)
      setItem(res.data)
    } catch (err) {
      setError(err.response?.status === 404 ? 'This link has expired or does not exist' : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  const copyLink = () => {
    navigator.clipboard.writeText(window.location.href)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-300 mb-4">404</h1>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold">{item?.title || 'Shared Item'}</h1>
            </div>
            <div className="flex items-center">
              <button
                onClick={copyLink}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                {copied ? '✓ Copied!' : 'Copy Link'}
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-4 text-sm text-gray-500">
            Shared by {item?.author?.name || 'Anonymous'} • {item?.createdAt ? new Date(item.createdAt).toLocaleDateString() : ''}
          </div>
          <div className="prose max-w-none">
            {item?.content || 'No content'}
          </div>
        </div>
      </main>
    </div>
  )
}"""

        else:
            # Generic page template
            return f"""import {{ useEffect, useState }} from 'react'
import {{ useNavigate, useParams }} from 'react-router-dom'
import {{ authService }} from '../services/auth'
import api from '../services/api'

export default function {name}() {{
  const navigate = useNavigate()
  const params = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {{
    if (!authService.isAuthenticated()) {{
      navigate('/login')
      return
    }}

    const fetchData = async () => {{
      try {{
        // TODO: Fetch data for this page
        // const response = await api.get('/api/...')
        // setData(response.data)
        setData({{ message: '{name} page loaded' }})
      }} catch (err) {{
        setError(err.response?.data?.error || 'Failed to load data')
      }} finally {{
        setLoading(false)
      }}
    }}

    fetchData()
  }}, [navigate, params])

  if (loading) {{
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }}

  if (error) {{
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {{error}}
        </div>
      </div>
    )
  }}

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold">{name}</h1>
            </div>
            <div className="flex items-center">
              <button
                onClick={{() => navigate('/')}}
                className="text-gray-600 hover:text-gray-900"
              >
                Back to Home
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold mb-4">{name}</h2>
            <p className="text-gray-600">This is the {name} page.</p>
            {{data && (
              <pre className="mt-4 p-4 bg-gray-100 rounded overflow-auto">
                {{JSON.stringify(data, null, 2)}}
              </pre>
            )}}
          </div>
        </div>
      </main>
    </div>
  )
}}"""

    def _generate_react_component(self, name: str) -> str:
        """Generate a React component dynamically."""
        name_lower = name.lower()

        # Special component implementations
        if name_lower == "navbar":
            return """import { Link, useNavigate } from 'react-router-dom'
import { authService } from '../services/auth'

export default function Navbar() {
  const navigate = useNavigate()
  const isAuthenticated = authService.isAuthenticated()

  const handleLogout = async () => {
    await authService.logout()
    navigate('/login')
  }

  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-bold text-gray-900">
              My App
            </Link>
            <div className="hidden md:flex ml-10 space-x-4">
              <Link to="/" className="text-gray-600 hover:text-gray-900 px-3 py-2">
                Home
              </Link>
              <Link to="/dashboard" className="text-gray-600 hover:text-gray-900 px-3 py-2">
                Dashboard
              </Link>
            </div>
          </div>
          <div className="flex items-center">
            {isAuthenticated ? (
              <button
                onClick={handleLogout}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              >
                Logout
              </button>
            ) : (
              <Link
                to="/login"
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}"""

        elif name_lower in ["taskcard", "card"]:
            return f"""export default function {name}({{ item, onEdit, onDelete }}) {{
  return (
    <div className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-semibold text-gray-900">{{item?.title || 'Untitled'}}</h3>
          <p className="text-sm text-gray-500 mt-1">{{item?.description || 'No description'}}</p>
        </div>
        <div className="flex gap-2">
          {{onEdit && (
            <button
              onClick={{() => onEdit(item)}}
              className="text-blue-500 hover:text-blue-700"
            >
              Edit
            </button>
          )}}
          {{onDelete && (
            <button
              onClick={{() => onDelete(item?.id)}}
              className="text-red-500 hover:text-red-700"
            >
              Delete
            </button>
          )}}
        </div>
      </div>
      {{item?.status && (
        <span className="inline-block mt-2 px-2 py-1 text-xs rounded bg-gray-100 text-gray-600">
          {{item.status}}
        </span>
      )}}
    </div>
  )
}}"""

        elif name_lower in ["commentsection", "comments"]:
            return f"""import {{ useState }} from 'react'

export default function {name}({{ comments = [], onAddComment }}) {{
  const [newComment, setNewComment] = useState('')

  const handleSubmit = (e) => {{
    e.preventDefault()
    if (newComment.trim() && onAddComment) {{
      onAddComment(newComment)
      setNewComment('')
    }}
  }}

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-semibold text-gray-900 mb-4">Comments</h3>

      <form onSubmit={{handleSubmit}} className="mb-4">
        <textarea
          value={{newComment}}
          onChange={{(e) => setNewComment(e.target.value)}}
          placeholder="Add a comment..."
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={{3}}
        />
        <button
          type="submit"
          className="mt-2 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Add Comment
        </button>
      </form>

      <div className="space-y-4">
        {{comments.length === 0 ? (
          <p className="text-gray-500">No comments yet</p>
        ) : (
          comments.map((comment, index) => (
            <div key={{index}} className="border-b pb-4">
              <p className="text-gray-800">{{comment.content}}</p>
              <p className="text-sm text-gray-500 mt-1">{{comment.author}} - {{comment.date}}</p>
            </div>
          ))
        )}}
      </div>
    </div>
  )
}}"""

        elif name_lower in ["fileupload", "upload"]:
            return f"""import {{ useState, useRef }} from 'react'

export default function {name}({{ onUpload, accept = '*', multiple = false }}) {{
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef(null)

  const handleChange = (e) => {{
    const selectedFiles = Array.from(e.target.files || [])
    setFiles(selectedFiles)
  }}

  const handleUpload = async () => {{
    if (files.length === 0 || !onUpload) return

    setUploading(true)
    try {{
      await onUpload(files)
      setFiles([])
      if (inputRef.current) inputRef.current.value = ''
    }} catch (err) {{
      console.error('Upload failed:', err)
    }} finally {{
      setUploading(false)
    }}
  }}

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
        <input
          ref={{inputRef}}
          type="file"
          accept={{accept}}
          multiple={{multiple}}
          onChange={{handleChange}}
          className="hidden"
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          className="cursor-pointer text-blue-500 hover:text-blue-600"
        >
          Click to select files
        </label>
        <p className="text-sm text-gray-500 mt-1">or drag and drop</p>
      </div>

      {{files.length > 0 && (
        <div className="mt-4">
          <p className="text-sm text-gray-600">Selected files:</p>
          <ul className="mt-2 space-y-1">
            {{files.map((file, index) => (
              <li key={{index}} className="text-sm text-gray-800">
                {{file.name}} ({{(file.size / 1024).toFixed(1)}} KB)
              </li>
            ))}}
          </ul>
          <button
            onClick={{handleUpload}}
            disabled={{uploading}}
            className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-blue-300"
          >
            {{uploading ? 'Uploading...' : 'Upload'}}
          </button>
        </div>
      )}}
    </div>
  )
}}"""

        else:
            # Generic component template
            return f"""import {{ useState }} from 'react'

export default function {name}({{ children, className = '', ...props }}) {{
  const [state, setState] = useState(null)

  return (
    <div className={{`bg-white rounded-lg shadow p-4 ${{className}}`}} {{...props}}>
      <h3 className="font-semibold text-gray-900 mb-2">{name}</h3>
      <div className="text-gray-600">
        {{children || 'Component content goes here'}}
      </div>
    </div>
  )
}}"""


    def _create_nextjs_frontend(self, design: Dict) -> Dict[str, bool]:
        """Create Next.js frontend."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = [
        "frontend/src/app",
        "frontend/src/components",
        "frontend/src/lib",
        "frontend/public"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        package_json = """{
      "name": "frontend",
      "version": "0.1.0",
      "private": true,
      "scripts": {
        "dev": "next dev",
        "build": "next build",
        "start": "next start"
      },
      "dependencies": {
        "next": "14.0.0",
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "axios": "^1.6.0"
      },
      "devDependencies": {
        "tailwindcss": "^3.3.0",
        "autoprefixer": "^10.4.0",
        "postcss": "^8.4.0"
      }
    }"""
        results["frontend/package.json"] = self._write_file("frontend/package.json", package_json)

        # next.config.js
        next_config = """/** @type {import('next').NextConfig} */
    const nextConfig = {}
    module.exports = nextConfig"""
        results["frontend/next.config.js"] = self._write_file("frontend/next.config.js", next_config)

        # tailwind.config.js
        tailwind_config = """/** @type {import('tailwindcss').Config} */
    module.exports = {
      content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
      theme: { extend: {} },
      plugins: [],
    }"""
        results["frontend/tailwind.config.js"] = self._write_file("frontend/tailwind.config.js", tailwind_config)

        # src/app/layout.jsx
        layout_jsx = """import './globals.css'

    export const metadata = {
      title: 'My App',
      description: 'Built with Next.js',
    }

    export default function RootLayout({ children }) {
      return (
        <html lang="en">
          <body>{children}</body>
        </html>
      )
    }"""
        results["frontend/src/app/layout.jsx"] = self._write_file("frontend/src/app/layout.jsx", layout_jsx)

        # src/app/globals.css
        globals_css = """@tailwind base;
    @tailwind components;
    @tailwind utilities;"""
        results["frontend/src/app/globals.css"] = self._write_file("frontend/src/app/globals.css", globals_css)

        # src/app/page.jsx
        page_jsx = """'use client'
    import { useRouter } from 'next/navigation'
    import { useEffect } from 'react'

    export default function Home() {
      const router = useRouter()

      useEffect(() => {
        const token = localStorage.getItem('token')
        if (!token) {
          router.push('/login')
        }
      }, [router])

      return (
        <div className="min-h-screen bg-gray-100">
          <h1 className="text-2xl font-bold p-8">Welcome to Next.js!</h1>
        </div>
      )
    }"""
        results["frontend/src/app/page.jsx"] = self._write_file("frontend/src/app/page.jsx", page_jsx)

        # src/app/login/page.jsx
        os.makedirs(os.path.join(self.project_dir, "frontend/src/app/login"), exist_ok=True)
        login_page = """'use client'
    import { useState } from 'react'
    import { useRouter } from 'next/navigation'

    export default function Login() {
      const router = useRouter()
      const [email, setEmail] = useState('')
      const [password, setPassword] = useState('')
      const [loading, setLoading] = useState(false)

      const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        // TODO: Call API
        router.push('/')
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
          <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-center mb-6">Login</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="w-full px-3 py-2 border rounded mb-4"
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="w-full px-3 py-2 border rounded mb-4"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
          >
            {loading ? 'Loading...' : 'Login'}
          </button>
        </form>
          </div>
        </div>
      )
    }"""
        results["frontend/src/app/login/page.jsx"] = self._write_file("frontend/src/app/login/page.jsx", login_page)

        results["frontend/.env.example"] = self._write_file("frontend/.env.example", "NEXT_PUBLIC_API_URL=http://localhost:8000")
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Next.js frontend[/#F1F5F9] ✓")
        return results

    def _create_vuejs_frontend(self, design: Dict) -> Dict[str, bool]:
        """Create Vue.js frontend."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = [
        "frontend/src/components",
        "frontend/src/views",
        "frontend/src/router",
        "frontend/src/services",
        "frontend/public"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        package_json = """{
      "name": "frontend",
      "version": "0.1.0",
      "private": true,
      "scripts": {
        "dev": "vite",
        "build": "vite build",
        "preview": "vite preview"
      },
      "dependencies": {
        "vue": "^3.3.0",
        "vue-router": "^4.2.0",
        "axios": "^1.6.0"
      },
      "devDependencies": {
        "@vitejs/plugin-vue": "^4.4.0",
        "vite": "^5.0.0",
        "tailwindcss": "^3.3.0",
        "autoprefixer": "^10.4.0",
        "postcss": "^8.4.0"
      }
    }"""
        results["frontend/package.json"] = self._write_file("frontend/package.json", package_json)

        # vite.config.js
        vite_config = """import { defineConfig } from 'vite'
    import vue from '@vitejs/plugin-vue'

    export default defineConfig({
      plugins: [vue()],
      server: { port: 3000 }
    })"""
        results["frontend/vite.config.js"] = self._write_file("frontend/vite.config.js", vite_config)

        # index.html
        index_html = """<!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Vue App</title>
      </head>
      <body>
        <div id="app"></div>
        <script type="module" src="/src/main.js"></script>
      </body>
    </html>"""
        results["frontend/index.html"] = self._write_file("frontend/index.html", index_html)

        # src/main.js
        main_js = """import { createApp } from 'vue'
    import App from './App.vue'
    import router from './router'
    import './style.css'

    createApp(App).use(router).mount('#app')"""
        results["frontend/src/main.js"] = self._write_file("frontend/src/main.js", main_js)

        # src/App.vue
        app_vue = """<template>
      <router-view />
    </template>

    <script>
    export default {
      name: 'App'
    }
    </script>"""
        results["frontend/src/App.vue"] = self._write_file("frontend/src/App.vue", app_vue)

        # src/style.css
        style_css = """@tailwind base;
    @tailwind components;
    @tailwind utilities;"""
        results["frontend/src/style.css"] = self._write_file("frontend/src/style.css", style_css)

        # src/router/index.js
        router_js = """import { createRouter, createWebHistory } from 'vue-router'
    import Home from '../views/Home.vue'
    import Login from '../views/Login.vue'

    const routes = [
      { path: '/', component: Home },
      { path: '/login', component: Login }
    ]

    const router = createRouter({
      history: createWebHistory(),
      routes
    })

    export default router"""
        results["frontend/src/router/index.js"] = self._write_file("frontend/src/router/index.js", router_js)

        # src/views/Home.vue
        home_vue = """<template>
      <div class="min-h-screen bg-gray-100">
        <div class="p-8">
          <h1 class="text-2xl font-bold">Welcome to Vue.js!</h1>
        </div>
      </div>
    </template>

    <script>
    export default {
      name: 'Home'
    }
    </script>"""
        results["frontend/src/views/Home.vue"] = self._write_file("frontend/src/views/Home.vue", home_vue)

        # src/views/Login.vue
        login_vue = """<template>
      <div class="min-h-screen flex items-center justify-center bg-gray-100">
        <div class="max-w-md w-full bg-white rounded-lg shadow-md p-8">
          <h2 class="text-2xl font-bold text-center mb-6">Login</h2>
          <form @submit.prevent="handleLogin">
        <input
          v-model="email"
          type="email"
          placeholder="Email"
          class="w-full px-3 py-2 border rounded mb-4"
          required
        />
        <input
          v-model="password"
          type="password"
          placeholder="Password"
          class="w-full px-3 py-2 border rounded mb-4"
          required
        />
        <button
          type="submit"
          class="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
        >
          Login
        </button>
          </form>
        </div>
      </div>
    </template>

    <script>
    export default {
      data() {
        return {
          email: '',
          password: ''
        }
      },
      methods: {
        handleLogin() {
          // TODO: Call API
          this.$router.push('/')
        }
      }
    }
    </script>"""
        results["frontend/src/views/Login.vue"] = self._write_file("frontend/src/views/Login.vue", login_vue)

        results["frontend/.env.example"] = self._write_file("frontend/.env.example", "VITE_API_URL=http://localhost:8000")
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Vue.js frontend[/#F1F5F9] ✓")
        return results

    def _create_angular_frontend(self, design: Dict) -> Dict[str, bool]:
        """Create Angular frontend."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = [
        "frontend/src/app/components",
        "frontend/src/app/services",
        "frontend/src/assets"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        package_json = """{
      "name": "frontend",
      "version": "0.0.0",
      "scripts": {
        "ng": "ng",
        "start": "ng serve",
        "build": "ng build",
        "watch": "ng build --watch --configuration development"
      },
      "private": true,
      "dependencies": {
        "@angular/animations": "^17.0.0",
        "@angular/common": "^17.0.0",
        "@angular/compiler": "^17.0.0",
        "@angular/core": "^17.0.0",
        "@angular/forms": "^17.0.0",
        "@angular/platform-browser": "^17.0.0",
        "@angular/platform-browser-dynamic": "^17.0.0",
        "@angular/router": "^17.0.0",
        "rxjs": "~7.8.0",
        "tslib": "^2.3.0",
        "zone.js": "~0.14.0"
      },
      "devDependencies": {
        "@angular-devkit/build-angular": "^17.0.0",
        "@angular/cli": "^17.0.0",
        "@angular/compiler-cli": "^17.0.0",
        "typescript": "~5.2.2"
      }
    }"""
        results["frontend/package.json"] = self._write_file("frontend/package.json", package_json)

        # angular.json
        angular_json = """{
      "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
      "version": 1,
      "newProjectRoot": "projects",
      "projects": {
        "frontend": {
          "projectType": "application",
          "root": "",
          "sourceRoot": "src",
          "prefix": "app",
          "architect": {
        "build": {
          "builder": "@angular-devkit/build-angular:browser",
          "options": {
            "outputPath": "dist/frontend",
            "index": "src/index.html",
            "main": "src/main.ts",
            "polyfills": ["zone.js"],
            "tsConfig": "tsconfig.app.json",
            "assets": ["src/assets"],
            "styles": ["src/styles.css"],
            "scripts": []
          }
        },
        "serve": {
          "builder": "@angular-devkit/build-angular:dev-server",
          "options": {
            "port": 3000
          }
        }
          }
        }
      }
    }"""
        results["frontend/angular.json"] = self._write_file("frontend/angular.json", angular_json)

        # tsconfig.json
        tsconfig = """{
      "compileOnSave": false,
      "compilerOptions": {
        "baseUrl": "./",
        "outDir": "./dist/out-tsc",
        "forceConsistentCasingInFileNames": true,
        "strict": true,
        "noImplicitOverride": true,
        "noPropertyAccessFromIndexSignature": true,
        "noImplicitReturns": true,
        "noFallthroughCasesInSwitch": true,
        "sourceMap": true,
        "declaration": false,
        "downlevelIteration": true,
        "experimentalDecorators": true,
        "moduleResolution": "node",
        "importHelpers": true,
        "target": "ES2022",
        "module": "ES2022",
        "useDefineForClassFields": false,
        "lib": ["ES2022", "dom"]
      }
    }"""
        results["frontend/tsconfig.json"] = self._write_file("frontend/tsconfig.json", tsconfig)

        # src/index.html
        index_html = """<!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>Angular App</title>
      <base href="/">
      <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
      <app-root></app-root>
    </body>
    </html>"""
        results["frontend/src/index.html"] = self._write_file("frontend/src/index.html", index_html)

        # src/main.ts
        main_ts = """import { bootstrapApplication } from '@angular/platform-browser';
    import { AppComponent } from './app/app.component';

    bootstrapApplication(AppComponent)
      .catch((err) => console.error(err));"""
        results["frontend/src/main.ts"] = self._write_file("frontend/src/main.ts", main_ts)

        # src/app/app.component.ts
        app_component = """import { Component } from '@angular/core';

    @Component({
      selector: 'app-root',
      standalone: true,
      template: '<h1>Welcome to Angular!</h1>',
      styles: []
    })
    export class AppComponent {
      title = 'frontend';
    }"""
        results["frontend/src/app/app.component.ts"] = self._write_file("frontend/src/app/app.component.ts", app_component)

        # src/styles.css
        styles_css = """* {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }"""
        results["frontend/src/styles.css"] = self._write_file("frontend/src/styles.css", styles_css)

        results["frontend/.env.example"] = self._write_file("frontend/.env.example", "API_URL=http://localhost:8000")
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Angular frontend[/#F1F5F9] ✓")
        return results

    def _create_svelte_frontend(self, design: Dict) -> Dict[str, bool]:
        """Create Svelte frontend."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = [
        "frontend/src/routes",
        "frontend/src/lib",
        "frontend/static"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        package_json = """{
      "name": "frontend",
      "version": "0.0.1",
      "private": true,
      "scripts": {
        "dev": "vite dev --port 3000",
        "build": "vite build",
        "preview": "vite preview"
      },
      "devDependencies": {
        "@sveltejs/adapter-auto": "^2.0.0",
        "@sveltejs/kit": "^1.20.0",
        "svelte": "^4.0.0",
        "vite": "^4.4.0"
      },
      "dependencies": {
        "axios": "^1.6.0"
      },
      "type": "module"
    }"""
        results["frontend/package.json"] = self._write_file("frontend/package.json", package_json)

        # svelte.config.js
        svelte_config = """import adapter from '@sveltejs/adapter-auto';

    export default {
      kit: {
        adapter: adapter()
      }
    };"""
        results["frontend/svelte.config.js"] = self._write_file("frontend/svelte.config.js", svelte_config)

        # vite.config.js
        vite_config = """import { sveltekit } from '@sveltejs/kit/vite';
    import { defineConfig } from 'vite';

    export default defineConfig({
      plugins: [sveltekit()]
    });"""
        results["frontend/vite.config.js"] = self._write_file("frontend/vite.config.js", vite_config)

        # src/routes/+page.svelte
        page_svelte = """<script>
      let count = 0;
    </script>

    <div class="container">
      <h1>Welcome to Svelte!</h1>
      <button on:click={() => count += 1}>
        Count: {count}
      </button>
    </div>

    <style>
      .container {
        padding: 2rem;
      }
      h1 {
        font-size: 2rem;
        font-weight: bold;
      }
    </style>"""
        results["frontend/src/routes/+page.svelte"] = self._write_file("frontend/src/routes/+page.svelte", page_svelte)

        # src/app.html
        app_html = """<!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width" />
        %sveltekit.head%
      </head>
      <body data-sveltekit-preload-data="hover">
        <div style="display: contents">%sveltekit.body%</div>
      </body>
    </html>"""
        results["frontend/src/app.html"] = self._write_file("frontend/src/app.html", app_html)

        results["frontend/.env.example"] = self._write_file("frontend/.env.example", "VITE_API_URL=http://localhost:8000")
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Svelte frontend[/#F1F5F9] ✓")
        return results

    def _create_react_native_frontend(self, design: Dict) -> Dict[str, bool]:
        """Create React Native mobile app."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = [
        "frontend/src/screens",
        "frontend/src/components",
        "frontend/src/services",
        "frontend/android",
        "frontend/ios"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        package_json = """{
      "name": "frontend",
      "version": "0.0.1",
      "private": true,
      "scripts": {
        "android": "react-native run-android",
        "ios": "react-native run-ios",
        "start": "react-native start"
      },
      "dependencies": {
        "react": "18.2.0",
        "react-native": "0.72.0",
        "@react-navigation/native": "^6.1.0",
        "@react-navigation/stack": "^6.3.0",
        "axios": "^1.6.0",
        "react-native-safe-area-context": "^4.7.0",
        "react-native-screens": "^3.25.0"
      },
      "devDependencies": {
        "@babel/core": "^7.20.0",
        "@babel/preset-env": "^7.20.0",
        "@babel/runtime": "^7.20.0",
        "metro-react-native-babel-preset": "0.76.0"
      }
    }"""
        results["frontend/package.json"] = self._write_file("frontend/package.json", package_json)

        # App.js
        app_js = """import React from 'react';
    import { NavigationContainer } from '@react-navigation/native';
    import { createStackNavigator } from '@react-navigation/stack';
    import HomeScreen from './src/screens/HomeScreen';
    import LoginScreen from './src/screens/LoginScreen';

    const Stack = createStackNavigator();

    export default function App() {
      return (
        <NavigationContainer>
          <Stack.Navigator initialRouteName="Login">
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Home" component={HomeScreen} />
          </Stack.Navigator>
        </NavigationContainer>
      );
    }"""
        results["frontend/App.js"] = self._write_file("frontend/App.js", app_js)

        # src/screens/HomeScreen.js
        home_screen = """import React from 'react';
    import { View, Text, StyleSheet } from 'react-native';

    export default function HomeScreen() {
      return (
        <View style={styles.container}>
          <Text style={styles.title}>Welcome to React Native!</Text>
        </View>
      );
    }

    const styles = StyleSheet.create({
      container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
      },
      title: {
        fontSize: 24,
        fontWeight: 'bold',
      },
    });"""
        results["frontend/src/screens/HomeScreen.js"] = self._write_file("frontend/src/screens/HomeScreen.js", home_screen)

        # src/screens/LoginScreen.js
        login_screen = """import React, { useState } from 'react';
    import { View, Text, TextInput, Button, StyleSheet } from 'react-native';

    export default function LoginScreen({ navigation }) {
      const [email, setEmail] = useState('');
      const [password, setPassword] = useState('');

      const handleLogin = () => {
        // TODO: Call API
        navigation.navigate('Home');
      };

      return (
        <View style={styles.container}>
          <Text style={styles.title}>Login</Text>
          <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
          />
          <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
          />
          <Button title="Login" onPress={handleLogin} />
        </View>
      );
    }

    const styles = StyleSheet.create({
      container: {
        flex: 1,
        justifyContent: 'center',
        padding: 20,
      },
      title: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 20,
        textAlign: 'center',
      },
      input: {
        borderWidth: 1,
        borderColor: '#ddd',
        padding: 10,
        marginBottom: 10,
        borderRadius: 5,
      },
    });"""
        results["frontend/src/screens/LoginScreen.js"] = self._write_file("frontend/src/screens/LoginScreen.js", login_screen)

        results["frontend/.env.example"] = self._write_file("frontend/.env.example", "API_URL=http://localhost:8000")
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created React Native frontend[/#F1F5F9] ✓")
        return results

    def _create_flutter_frontend(self, design: Dict) -> Dict[str, bool]:
        """Create Flutter mobile app."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = [
        "frontend/lib/screens",
        "frontend/lib/services",
        "frontend/lib/widgets",
        "frontend/android",
        "frontend/ios"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        # pubspec.yaml
        pubspec = """name: frontend
    description: Flutter mobile app
    publish_to: 'none'
    version: 1.0.0+1

    environment:
      sdk: '>=3.0.0 <4.0.0'

    dependencies:
      flutter:
        sdk: flutter
      http: ^1.1.0
      provider: ^6.0.0

    dev_dependencies:
      flutter_test:
        sdk: flutter
      flutter_lints: ^2.0.0

    flutter:
      uses-material-design: true"""
        results["frontend/pubspec.yaml"] = self._write_file("frontend/pubspec.yaml", pubspec)

        # lib/main.dart
        main_dart = """import 'package:flutter/material.dart';
    import 'screens/login_screen.dart';
    import 'screens/home_screen.dart';

    void main() {
      runApp(const MyApp());
    }

    class MyApp extends StatelessWidget {
      const MyApp({super.key});

      @override
      Widget build(BuildContext context) {
        return MaterialApp(
          title: 'Flutter App',
          theme: ThemeData(
        primarySwatch: Colors.blue,
          ),
          initialRoute: '/login',
          routes: {
        '/login': (context) => const LoginScreen(),
        '/home': (context) => const HomeScreen(),
          },
        );
      }
    }"""
        results["frontend/lib/main.dart"] = self._write_file("frontend/lib/main.dart", main_dart)

        # lib/screens/login_screen.dart
        login_screen = """import 'package:flutter/material.dart';

    class LoginScreen extends StatefulWidget {
      const LoginScreen({super.key});

      @override
      State<LoginScreen> createState() => _LoginScreenState();
    }

    class _LoginScreenState extends State<LoginScreen> {
      final _emailController = TextEditingController();
      final _passwordController = TextEditingController();

      void _handleLogin() {
        // TODO: Call API
        Navigator.pushReplacementNamed(context, '/home');
      }

      @override
      Widget build(BuildContext context) {
        return Scaffold(
          body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'Login',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(
                labelText: 'Email',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _passwordController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Password',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _handleLogin,
              child: const Text('Login'),
            ),
          ],
        ),
          ),
        );
      }
    }"""
        results["frontend/lib/screens/login_screen.dart"] = self._write_file("frontend/lib/screens/login_screen.dart", login_screen)

        # lib/screens/home_screen.dart
        home_screen = """import 'package:flutter/material.dart';

    class HomeScreen extends StatelessWidget {
      const HomeScreen({super.key});

      @override
      Widget build(BuildContext context) {
        return Scaffold(
          appBar: AppBar(
        title: const Text('Home'),
          ),
          body: const Center(
        child: Text(
          'Welcome to Flutter!',
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
          ),
        );
      }
    }"""
        results["frontend/lib/screens/home_screen.dart"] = self._write_file("frontend/lib/screens/home_screen.dart", home_screen)

        results["frontend/.env.example"] = self._write_file("frontend/.env.example", "API_URL=http://localhost:8000")
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Flutter frontend[/#F1F5F9] ✓")
        return results

    def _create_swift_frontend(self, design: Dict) -> Dict[str, bool]:
        """Create Swift iOS app DYNAMICALLY from design."""
        results = {}
        from rich.console import Console
        console = Console()

        # Get pages from design
        pages = design.get("pages", ["Login", "Home"])
        page_names = []
        for page in pages:
            if isinstance(page, dict):
                name = page.get("name", "View")
            else:
                name = str(page).replace(" ", "")
            if name and name not in page_names:
                page_names.append(name)

        # Ensure Login is included
        if "Login" not in page_names:
            page_names.insert(0, "Login")

        folders = [
            "ios/App",
            "ios/Views",
            "ios/Services",
            "ios/Models",
            "ios/Components"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)
        console.print(f"[#A855F7]⏺[/#A855F7] Created iOS folders ✓")

        # App/App.swift (SwiftUI App)
        view_imports = "\n".join([f"        {name}View()" for name in page_names[:3]])
        app_swift = f"""import SwiftUI

    @main
struct MainApp: App {{
    @StateObject private var authManager = AuthManager()

    var body: some Scene {{
        WindowGroup {{
            if authManager.isAuthenticated {{
                ContentView()
                    .environmentObject(authManager)
            }} else {{
                LoginView()
                    .environmentObject(authManager)
            }}
        }}
    }}
}}
"""
        results["ios/App/App.swift"] = self._write_file("ios/App/App.swift", app_swift)
        console.print(f"[#A855F7]⏺[/#A855F7] Created: ios/App/App.swift ✓")

        # ContentView.swift with TabView
        tabs = "\n            ".join([f'Tab("{name}", systemImage: "{self._get_sf_symbol(name)}") {{\n                {name}View()\n            }}' for name in page_names if name != "Login"])
        content_view = f"""import SwiftUI

struct ContentView: View {{
    @EnvironmentObject var authManager: AuthManager

    var body: some View {{
        TabView {{
            {tabs}
        }}
    }}
}}

#Preview {{
    ContentView()
        .environmentObject(AuthManager())
}}
"""
        results["ios/Views/ContentView.swift"] = self._write_file("ios/Views/ContentView.swift", content_view)
        console.print(f"[#A855F7]⏺[/#A855F7] Created: ios/Views/ContentView.swift ✓")

        # Generate each view dynamically
        for page_name in page_names:
            view_content = self._generate_swift_view(page_name)
            results[f"ios/Views/{page_name}View.swift"] = self._write_file(f"ios/Views/{page_name}View.swift", view_content)
            console.print(f"[#A855F7]⏺[/#A855F7] Created: ios/Views/{page_name}View.swift ✓")

        # Services/AuthManager.swift
        auth_manager = """import Foundation
import SwiftUI

class AuthManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var isLoading = false
    @Published var error: String?

    private let apiService = APIService.shared

    func login(email: String, password: String) async {
        isLoading = true
        error = nil

        do {
            let user = try await apiService.login(email: email, password: password)
            DispatchQueue.main.async {
                self.currentUser = user
                self.isAuthenticated = true
                self.isLoading = false
            }
        } catch {
            DispatchQueue.main.async {
                self.error = error.localizedDescription
                self.isLoading = false
            }
        }
    }

    func logout() {
        isAuthenticated = false
        currentUser = nil
        apiService.clearToken()
    }
}
"""
        results["ios/Services/AuthManager.swift"] = self._write_file("ios/Services/AuthManager.swift", auth_manager)
        console.print(f"[#A855F7]⏺[/#A855F7] Created: ios/Services/AuthManager.swift ✓")

        # Services/APIService.swift
        api_service = """import Foundation

class APIService {
    static let shared = APIService()
    private let baseURL = "http://localhost:8000/api"
    private var token: String?

    private init() {}

    func setToken(_ token: String) {
        self.token = token
    }

    func clearToken() {
        self.token = nil
    }

    func login(email: String, password: String) async throws -> User {
        let url = URL(string: "\\(baseURL)/auth/login")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["email": email, "password": password]
        request.httpBody = try JSONEncoder().encode(body)

        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(LoginResponse.self, from: data)
        setToken(response.token)
        return response.user
    }

    func get<T: Decodable>(_ endpoint: String) async throws -> T {
        let url = URL(string: "\\(baseURL)\\(endpoint)")!
        var request = URLRequest(url: url)
        if let token = token {
            request.setValue("Bearer \\(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(T.self, from: data)
    }
}

struct LoginResponse: Codable {
    let token: String
    let user: User
}
"""
        results["ios/Services/APIService.swift"] = self._write_file("ios/Services/APIService.swift", api_service)
        console.print(f"[#A855F7]⏺[/#A855F7] Created: ios/Services/APIService.swift ✓")

        # Models/User.swift
        user_model = """import Foundation

struct User: Codable, Identifiable {
    let id: String
    let email: String
    let name: String
    var avatar: String?
    let createdAt: Date?

    enum CodingKeys: String, CodingKey {
        case id, email, name, avatar
        case createdAt = "created_at"
    }
}
"""
        results["ios/Models/User.swift"] = self._write_file("ios/Models/User.swift", user_model)
        console.print(f"[#A855F7]⏺[/#A855F7] Created: ios/Models/User.swift ✓")

        # .env.example for iOS
        env_example = """# iOS App Environment
API_BASE_URL=http://localhost:8000/api
"""
        results["ios/.env.example"] = self._write_file("ios/.env.example", env_example)

        # README.md
        readme = f"""# iOS App (Swift/SwiftUI)

## Views Created
{chr(10).join([f"- {name}View" for name in page_names])}

## Setup

1. Open `ios` folder in Xcode
2. Build and run on simulator or device

## Requirements

- Xcode 15+
- iOS 17+
- Swift 5.9+

## Architecture

- SwiftUI with MVVM pattern
- Async/await for networking
- @EnvironmentObject for state management
"""
        results["ios/README.md"] = self._write_file("ios/README.md", readme)

        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Swift iOS app[/#F1F5F9] ✓")
        console.print(f"[green]✅ iOS: {len(results)} files created[/green]")
        return results

    def _get_sf_symbol(self, page_name: str) -> str:
        """Get SF Symbol icon for page name."""
        icons = {
            "home": "house.fill",
            "dashboard": "square.grid.2x2.fill",
            "profile": "person.fill",
            "settings": "gear",
            "search": "magnifyingglass",
            "list": "list.bullet",
            "calendar": "calendar",
            "message": "message.fill",
            "notification": "bell.fill",
            "cart": "cart.fill",
            "favorite": "heart.fill",
            "bookmark": "bookmark.fill"
        }
        return icons.get(page_name.lower(), "star.fill")

    def _generate_swift_view(self, page_name: str) -> str:
        """Generate Swift view based on page name."""
        if page_name.lower() == "login":
            return """import SwiftUI

    struct LoginView: View {
    @EnvironmentObject var authManager: AuthManager
        @State private var email = ""
        @State private var password = ""

        var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Spacer()

                // Logo
                Image(systemName: "person.circle.fill")
                    .font(.system(size: 80))
                    .foregroundColor(.blue)

                Text("Welcome Back")
                .font(.largeTitle)
                .fontWeight(.bold)

                // Form
                VStack(spacing: 16) {
            TextField("Email", text: $email)
                        .textFieldStyle(.roundedBorder)
                        .textContentType(.emailAddress)
                .autocapitalization(.none)

            SecureField("Password", text: $password)
                        .textFieldStyle(.roundedBorder)
                        .textContentType(.password)
                }
                .padding(.horizontal)

                // Login Button
                Button(action: {
                    Task {
                        await authManager.login(email: email, password: password)
                    }
                }) {
                    if authManager.isLoading {
                        ProgressView()
                            .tint(.white)
                    } else {
                        Text("Login")
                            .fontWeight(.semibold)
                    }
                }
                .frame(maxWidth: .infinity)
            .padding()
            .background(Color.blue)
            .foregroundColor(.white)
                .cornerRadius(12)
                .padding(.horizontal)
                .disabled(authManager.isLoading)

                // Error
                if let error = authManager.error {
                    Text(error)
                        .foregroundColor(.red)
                        .font(.caption)
                }

                Spacer()

                // Register Link
                NavigationLink("Don't have an account? Register") {
                    RegisterView()
                }
                .padding(.bottom)
            }
            .navigationTitle("Login")
            .navigationBarHidden(true)
        }
    }
}

#Preview {
    LoginView()
        .environmentObject(AuthManager())
}
"""
        elif page_name.lower() == "register":
            return """import SwiftUI

struct RegisterView: View {
    @Environment(\\.dismiss) var dismiss
    @State private var name = ""
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""

        var body: some View {
        VStack(spacing: 24) {
            Text("Create Account")
                .font(.largeTitle)
                    .fontWeight(.bold)

            VStack(spacing: 16) {
                TextField("Name", text: $name)
                    .textFieldStyle(.roundedBorder)

                TextField("Email", text: $email)
                    .textFieldStyle(.roundedBorder)
                    .textContentType(.emailAddress)
                    .autocapitalization(.none)

                SecureField("Password", text: $password)
                    .textFieldStyle(.roundedBorder)

                SecureField("Confirm Password", text: $confirmPassword)
                    .textFieldStyle(.roundedBorder)
            }
            .padding(.horizontal)

            Button("Register") {
                // TODO: Register API call
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color.blue)
            .foregroundColor(.white)
            .cornerRadius(12)
            .padding(.horizontal)

            Spacer()
        }
        .padding(.top, 40)
        .navigationTitle("Register")
        .navigationBarTitleDisplayMode(.inline)
    }
}

#Preview {
    NavigationStack {
        RegisterView()
    }
}
"""
        elif page_name.lower() in ["dashboard", "home"]:
            return f"""import SwiftUI

struct {page_name}View: View {{
    @EnvironmentObject var authManager: AuthManager
    @State private var items: [String] = []
    @State private var isLoading = true

    var body: some View {{
        NavigationStack {{
            Group {{
                if isLoading {{
                    ProgressView()
                }} else {{
                    ScrollView {{
                        LazyVStack(spacing: 16) {{
                            // Stats Cards
                            HStack(spacing: 16) {{
                                StatCard(title: "Total", value: "42", icon: "chart.bar.fill", color: .blue)
                                StatCard(title: "Active", value: "12", icon: "checkmark.circle.fill", color: .green)
                            }}
                            .padding(.horizontal)

                            // Content List
                            ForEach(items, id: \\.self) {{ item in
                                ItemCard(title: item)
                            }}
                        }}
                        .padding(.top)
                    }}
                }}
            }}
            .navigationTitle("{page_name}")
            .toolbar {{
                ToolbarItem(placement: .navigationBarTrailing) {{
                    Button(action: {{ authManager.logout() }}) {{
                        Image(systemName: "rectangle.portrait.and.arrow.right")
                    }}
                }}
            }}
        }}
        .onAppear {{ loadData() }}
    }}

    func loadData() {{
        // TODO: Fetch from API
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {{
            items = ["Item 1", "Item 2", "Item 3"]
            isLoading = false
        }}
    }}
}}

struct StatCard: View {{
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {{
        VStack(alignment: .leading, spacing: 8) {{
            HStack {{
                Image(systemName: icon)
                    .foregroundColor(color)
                Spacer()
            }}
            Text(value)
                .font(.title)
                .fontWeight(.bold)
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }}
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }}
}}

struct ItemCard: View {{
    let title: String

    var body: some View {{
        HStack {{
            Text(title)
            Spacer()
            Image(systemName: "chevron.right")
                .foregroundColor(.secondary)
        }}
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.05), radius: 5)
        .padding(.horizontal)
    }}
}}

#Preview {{
    {page_name}View()
        .environmentObject(AuthManager())
}}
"""
        else:
            # Generic view template
            return f"""import SwiftUI

struct {page_name}View: View {{
    @EnvironmentObject var authManager: AuthManager
    @State private var isLoading = true

    var body: some View {{
        NavigationStack {{
            ScrollView {{
                VStack(spacing: 20) {{
                    if isLoading {{
                        ProgressView()
                    }} else {{
                        // Content
                        Text("{page_name}")
                            .font(.title)
                            .fontWeight(.bold)

                        // TODO: Add {page_name} content
                        ContentPlaceholder()
                    }}
                }}
                .padding()
            }}
            .navigationTitle("{page_name}")
        }}
        .onAppear {{ loadData() }}
    }}

    func loadData() {{
        // TODO: Fetch data from API
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {{
            isLoading = false
        }}
    }}
}}

struct ContentPlaceholder: View {{
    var body: some View {{
        VStack(spacing: 16) {{
            ForEach(0..<3) {{ _ in
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color(.systemGray5))
                    .frame(height: 100)
            }}
        }}
    }}
}}

#Preview {{
    {page_name}View()
        .environmentObject(AuthManager())
}}
"""

    def _create_kotlin_frontend(self, design: Dict) -> Dict[str, bool]:
        """Create dynamic Kotlin Android app based on design pages."""
        results = {}
        from rich.console import Console
        console = Console()

        # Get project info
        project_info = self.storage.load("project_info") or self.storage.load("project") or {}
        project_name = project_info.get("name", design.get("name", "MyApp"))
        package_name = project_name.lower().replace(" ", "").replace("-", "")
        package_path = f"com.{package_name}"

        # Get pages from design
        pages = design.get("pages", [])
        components = design.get("components", [])

        # Normalize pages
        page_list = []
        for page in pages:
            if isinstance(page, dict):
                page_list.append({
                    "name": page.get("name", "Page"),
                    "path": page.get("path", "/"),
                    "description": page.get("description", "")
                })
            else:
                page_list.append({
                    "name": str(page),
                    "path": f"/{str(page).lower().replace(' ', '-')}",
                    "description": f"{page} screen"
                })

        # Default pages if none provided
        if not page_list:
            page_list = [
                {"name": "Login", "path": "/login", "description": "User login screen"},
                {"name": "Register", "path": "/register", "description": "User registration screen"},
                {"name": "Dashboard", "path": "/dashboard", "description": "Main dashboard"},
                {"name": "Profile", "path": "/profile", "description": "User profile"},
                {"name": "Settings", "path": "/settings", "description": "App settings"}
            ]

        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Creating Kotlin Android frontend: {project_name}[/#F1F5F9]")

        # Create folders
        folders = [
            f"frontend/app/src/main/java/com/{package_name}",
            f"frontend/app/src/main/java/com/{package_name}/ui/activities",
            f"frontend/app/src/main/java/com/{package_name}/ui/fragments",
            f"frontend/app/src/main/java/com/{package_name}/ui/adapters",
            f"frontend/app/src/main/java/com/{package_name}/data/api",
            f"frontend/app/src/main/java/com/{package_name}/data/models",
            f"frontend/app/src/main/java/com/{package_name}/data/repository",
            f"frontend/app/src/main/java/com/{package_name}/utils",
            "frontend/app/src/main/res/layout",
            "frontend/app/src/main/res/values",
            "frontend/app/src/main/res/drawable",
            "frontend/app/src/main/res/navigation"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Android folders[/#F1F5F9] ✓")

        # Project-level build.gradle
        project_build_gradle = f"""// Top-level build file
plugins {{
    id 'com.android.application' version '8.1.2' apply false
    id 'org.jetbrains.kotlin.android' version '1.9.0' apply false
    id 'com.google.dagger.hilt.android' version '2.48' apply false
}}

task clean(type: Delete) {{
    delete rootProject.buildDir
}}
"""
        results["frontend/build.gradle"] = self._write_file("frontend/build.gradle", project_build_gradle)

        # App-level build.gradle with dependencies
        app_build_gradle = f"""plugins {{
        id 'com.android.application'
        id 'org.jetbrains.kotlin.android'
    id 'kotlin-kapt'
    id 'com.google.dagger.hilt.android'
}}

android {{
    namespace '{package_path}'
        compileSdk 34

    defaultConfig {{
        applicationId "{package_path}"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"

        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
    }}

    buildTypes {{
        release {{
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
    }}

    buildFeatures {{
        viewBinding true
        dataBinding true
    }}

    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }}

    kotlinOptions {{
        jvmTarget = '17'
    }}
}}

dependencies {{
    // Core Android
        implementation 'androidx.core:core-ktx:1.12.0'
        implementation 'androidx.appcompat:appcompat:1.6.1'
        implementation 'com.google.android.material:material:1.10.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'

    // Navigation
    implementation 'androidx.navigation:navigation-fragment-ktx:2.7.5'
    implementation 'androidx.navigation:navigation-ui-ktx:2.7.5'

    // Lifecycle
    implementation 'androidx.lifecycle:lifecycle-viewmodel-ktx:2.6.2'
    implementation 'androidx.lifecycle:lifecycle-livedata-ktx:2.6.2'
    implementation 'androidx.lifecycle:lifecycle-runtime-ktx:2.6.2'

    // Networking
        implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'com.squareup.okhttp3:logging-interceptor:4.11.0'

    // Coroutines
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3'
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3'

    // Hilt DI
    implementation 'com.google.dagger:hilt-android:2.48'
    kapt 'com.google.dagger:hilt-compiler:2.48'

    // Image Loading
    implementation 'io.coil-kt:coil:2.5.0'

    // DataStore
    implementation 'androidx.datastore:datastore-preferences:1.0.0'

    // Testing
    testImplementation 'junit:junit:4.13.2'
    androidTestImplementation 'androidx.test.ext:junit:1.1.5'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.5.1'
}}
"""
        results["frontend/app/build.gradle"] = self._write_file("frontend/app/build.gradle", app_build_gradle)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created: build.gradle files[/#F1F5F9] ✓")

        # settings.gradle
        settings_gradle = f"""pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}

dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}

rootProject.name = "{project_name}"
include ':app'
"""
        results["frontend/settings.gradle"] = self._write_file("frontend/settings.gradle", settings_gradle)

        # gradle.properties
        gradle_properties = """org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
"""
        results["frontend/gradle.properties"] = self._write_file("frontend/gradle.properties", gradle_properties)

        # Generate activity list for manifest
        activity_declarations = ""
        for page in page_list:
            page_name = page["name"].replace(" ", "").replace("/", "")
            activity_declarations += f"""
        <activity
            android:name=".ui.activities.{page_name}Activity"
            android:exported="false"
            android:theme="@style/Theme.{project_name.replace(' ', '')}" />"""

        # AndroidManifest.xml
        android_manifest = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <application
        android:name=".{project_name.replace(' ', '')}Application"
        android:allowBackup="true"
        android:dataExtractionRules="@xml/data_extraction_rules"
        android:fullBackupContent="@xml/backup_rules"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.{project_name.replace(' ', '')}"
        tools:targetApi="31">

        <activity
            android:name=".ui.activities.MainActivity"
            android:exported="true"
            android:theme="@style/Theme.{project_name.replace(' ', '')}">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity
            android:name=".ui.activities.LoginActivity"
            android:exported="false"
            android:theme="@style/Theme.{project_name.replace(' ', '')}" />

        <activity
            android:name=".ui.activities.RegisterActivity"
            android:exported="false"
            android:theme="@style/Theme.{project_name.replace(' ', '')}" />{activity_declarations}
    </application>

</manifest>
"""
        results["frontend/app/src/main/AndroidManifest.xml"] = self._write_file("frontend/app/src/main/AndroidManifest.xml", android_manifest)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created: AndroidManifest.xml[/#F1F5F9] ✓")

        # Application class with Hilt
        application_class = f"""package {package_path}

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class {project_name.replace(' ', '')}Application : Application() {{

    override fun onCreate() {{
        super.onCreate()
        // Initialize any global services here
    }}
}}
"""
        results[f"frontend/app/src/main/java/com/{package_name}/{project_name.replace(' ', '')}Application.kt"] = self._write_file(f"frontend/app/src/main/java/com/{package_name}/{project_name.replace(' ', '')}Application.kt", application_class)

        # User Model
        user_model = f"""package {package_path}.data.models

import com.google.gson.annotations.SerializedName

data class User(
    @SerializedName("id")
    val id: String,

    @SerializedName("email")
    val email: String,

    @SerializedName("name")
    val name: String,

    @SerializedName("avatar")
    val avatar: String? = null,

    @SerializedName("created_at")
    val createdAt: String? = null
)

data class LoginRequest(
    val email: String,
    val password: String
)

data class RegisterRequest(
    val email: String,
    val password: String,
    val name: String
)

data class AuthResponse(
    val user: User,
    val token: String,
    val message: String? = null
)

data class ApiResponse<T>(
    val success: Boolean,
    val data: T?,
    val message: String?
)
"""
        results[f"frontend/app/src/main/java/com/{package_name}/data/models/User.kt"] = self._write_file(f"frontend/app/src/main/java/com/{package_name}/data/models/User.kt", user_model)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created: User.kt model[/#F1F5F9] ✓")

        # API Service with Retrofit
        api_service = f"""package {package_path}.data.api

import {package_path}.data.models.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {{

    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): Response<AuthResponse>

    @POST("auth/register")
    suspend fun register(@Body request: RegisterRequest): Response<AuthResponse>

    @GET("auth/me")
    suspend fun getCurrentUser(): Response<ApiResponse<User>>

    @POST("auth/logout")
    suspend fun logout(): Response<ApiResponse<Unit>>

    @GET("users/{{id}}")
    suspend fun getUser(@Path("id") userId: String): Response<ApiResponse<User>>

    @PUT("users/{{id}}")
    suspend fun updateUser(
        @Path("id") userId: String,
        @Body user: User
    ): Response<ApiResponse<User>>
}}
"""
        results[f"frontend/app/src/main/java/com/{package_name}/data/api/ApiService.kt"] = self._write_file(f"frontend/app/src/main/java/com/{package_name}/data/api/ApiService.kt", api_service)

        # Network Module for Hilt DI
        network_module = f"""package {package_path}.data.api

import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {{

    private const val BASE_URL = "http://10.0.2.2:8000/api/" // Android emulator localhost

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {{
        val loggingInterceptor = HttpLoggingInterceptor().apply {{
            level = HttpLoggingInterceptor.Level.BODY
        }}

        return OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .addInterceptor {{ chain ->
                val original = chain.request()
                val token = TokenManager.getToken()

                val request = if (token != null) {{
                    original.newBuilder()
                        .header("Authorization", "Bearer $token")
                        .build()
                }} else {{
                    original
                }}

                chain.proceed(request)
            }}
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }}

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit {{
        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }}

    @Provides
    @Singleton
    fun provideApiService(retrofit: Retrofit): ApiService {{
        return retrofit.create(ApiService::class.java)
    }}
}}

object TokenManager {{
    private var token: String? = null

    fun setToken(newToken: String?) {{
        token = newToken
    }}

    fun getToken(): String? = token

    fun clearToken() {{
        token = null
    }}
}}
"""
        results[f"frontend/app/src/main/java/com/{package_name}/data/api/NetworkModule.kt"] = self._write_file(f"frontend/app/src/main/java/com/{package_name}/data/api/NetworkModule.kt", network_module)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created: ApiService.kt & NetworkModule.kt[/#F1F5F9] ✓")

        # Auth Repository
        auth_repository = f"""package {package_path}.data.repository

import {package_path}.data.api.ApiService
import {package_path}.data.api.TokenManager
import {package_path}.data.models.*
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val apiService: ApiService
) {{

    suspend fun login(email: String, password: String): Result<AuthResponse> {{
        return try {{
            val response = apiService.login(LoginRequest(email, password))
            if (response.isSuccessful && response.body() != null) {{
                val authResponse = response.body()!!
                TokenManager.setToken(authResponse.token)
                Result.success(authResponse)
            }} else {{
                Result.failure(Exception(response.message()))
            }}
        }} catch (e: Exception) {{
            Result.failure(e)
        }}
    }}

    suspend fun register(email: String, password: String, name: String): Result<AuthResponse> {{
        return try {{
            val response = apiService.register(RegisterRequest(email, password, name))
            if (response.isSuccessful && response.body() != null) {{
                val authResponse = response.body()!!
                TokenManager.setToken(authResponse.token)
                Result.success(authResponse)
            }} else {{
                Result.failure(Exception(response.message()))
            }}
        }} catch (e: Exception) {{
            Result.failure(e)
        }}
    }}

    suspend fun logout(): Result<Unit> {{
        return try {{
            apiService.logout()
            TokenManager.clearToken()
            Result.success(Unit)
        }} catch (e: Exception) {{
            TokenManager.clearToken()
            Result.success(Unit)
        }}
    }}

    suspend fun getCurrentUser(): Result<User> {{
        return try {{
            val response = apiService.getCurrentUser()
            if (response.isSuccessful && response.body()?.data != null) {{
                Result.success(response.body()!!.data!!)
            }} else {{
                Result.failure(Exception("Failed to get user"))
            }}
        }} catch (e: Exception) {{
            Result.failure(e)
        }}
    }}

    fun isLoggedIn(): Boolean = TokenManager.getToken() != null
}}
"""
        results[f"frontend/app/src/main/java/com/{package_name}/data/repository/AuthRepository.kt"] = self._write_file(f"frontend/app/src/main/java/com/{package_name}/data/repository/AuthRepository.kt", auth_repository)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created: AuthRepository.kt[/#F1F5F9] ✓")

        # MainActivity with Navigation
        main_activity = f"""package {package_path}.ui.activities

import android.content.Intent
    import android.os.Bundle
    import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import {package_path}.data.repository.AuthRepository
import {package_path}.databinding.ActivityMainBinding
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : AppCompatActivity() {{

    private lateinit var binding: ActivityMainBinding

    @Inject
    lateinit var authRepository: AuthRepository

    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        checkAuthState()
    }}

    private fun checkAuthState() {{
        lifecycleScope.launch {{
            if (authRepository.isLoggedIn()) {{
                // Already logged in, show main content
                setupMainContent()
            }} else {{
                // Not logged in, go to login
                startActivity(Intent(this@MainActivity, LoginActivity::class.java))
                finish()
            }}
        }}
    }}

    private fun setupMainContent() {{
        // Setup bottom navigation or main UI
        binding.welcomeText.text = "Welcome to {project_name}!"
    }}
}}
"""
        results[f"frontend/app/src/main/java/com/{package_name}/ui/activities/MainActivity.kt"] = self._write_file(f"frontend/app/src/main/java/com/{package_name}/ui/activities/MainActivity.kt", main_activity)

        # LoginActivity
        login_activity = f"""package {package_path}.ui.activities

import android.content.Intent
    import android.os.Bundle
import android.widget.Toast
    import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import {package_path}.data.repository.AuthRepository
import {package_path}.databinding.ActivityLoginBinding
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class LoginActivity : AppCompatActivity() {{

    private lateinit var binding: ActivityLoginBinding

    @Inject
    lateinit var authRepository: AuthRepository

    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupViews()
    }}

    private fun setupViews() {{
        binding.loginButton.setOnClickListener {{
            val email = binding.emailInput.text.toString().trim()
            val password = binding.passwordInput.text.toString()

            if (email.isEmpty() || password.isEmpty()) {{
                Toast.makeText(this, "Please fill in all fields", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }}

            performLogin(email, password)
        }}

        binding.registerLink.setOnClickListener {{
            startActivity(Intent(this, RegisterActivity::class.java))
        }}
    }}

    private fun performLogin(email: String, password: String) {{
        binding.loginButton.isEnabled = false

        lifecycleScope.launch {{
            val result = authRepository.login(email, password)

            result.onSuccess {{
                Toast.makeText(this@LoginActivity, "Login successful!", Toast.LENGTH_SHORT).show()
                startActivity(Intent(this@LoginActivity, MainActivity::class.java))
                finish()
            }}

            result.onFailure {{ error ->
                Toast.makeText(this@LoginActivity, error.message ?: "Login failed", Toast.LENGTH_SHORT).show()
                binding.loginButton.isEnabled = true
            }}
        }}
    }}
}}
"""
        results[f"frontend/app/src/main/java/com/{package_name}/ui/activities/LoginActivity.kt"] = self._write_file(f"frontend/app/src/main/java/com/{package_name}/ui/activities/LoginActivity.kt", login_activity)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created: LoginActivity.kt[/#F1F5F9] ✓")

        # RegisterActivity
        register_activity = f"""package {package_path}.ui.activities

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import {package_path}.data.repository.AuthRepository
import {package_path}.databinding.ActivityRegisterBinding
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class RegisterActivity : AppCompatActivity() {{

    private lateinit var binding: ActivityRegisterBinding

    @Inject
    lateinit var authRepository: AuthRepository

    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        binding = ActivityRegisterBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupViews()
    }}

    private fun setupViews() {{
        binding.registerButton.setOnClickListener {{
            val name = binding.nameInput.text.toString().trim()
            val email = binding.emailInput.text.toString().trim()
            val password = binding.passwordInput.text.toString()
            val confirmPassword = binding.confirmPasswordInput.text.toString()

            if (name.isEmpty() || email.isEmpty() || password.isEmpty()) {{
                Toast.makeText(this, "Please fill in all fields", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }}

            if (password != confirmPassword) {{
                Toast.makeText(this, "Passwords do not match", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }}

            performRegister(email, password, name)
        }}

        binding.loginLink.setOnClickListener {{
            finish()
        }}
    }}

    private fun performRegister(email: String, password: String, name: String) {{
        binding.registerButton.isEnabled = false

        lifecycleScope.launch {{
            val result = authRepository.register(email, password, name)

            result.onSuccess {{
                Toast.makeText(this@RegisterActivity, "Registration successful!", Toast.LENGTH_SHORT).show()
                startActivity(Intent(this@RegisterActivity, MainActivity::class.java))
                finishAffinity()
            }}

            result.onFailure {{ error ->
                Toast.makeText(this@RegisterActivity, error.message ?: "Registration failed", Toast.LENGTH_SHORT).show()
                binding.registerButton.isEnabled = true
            }}
        }}
    }}
}}
"""
        results[f"frontend/app/src/main/java/com/{package_name}/ui/activities/RegisterActivity.kt"] = self._write_file(f"frontend/app/src/main/java/com/{package_name}/ui/activities/RegisterActivity.kt", register_activity)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created: RegisterActivity.kt[/#F1F5F9] ✓")

        # Generate activities for each page from design
        for page in page_list:
            page_name = page["name"].replace(" ", "").replace("/", "")
            # Skip Login, Register, Dashboard as they're already created
            if page_name.lower() in ["login", "register", "dashboard", "main"]:
                continue

            activity_content = f"""package {package_path}.ui.activities

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import {package_path}.databinding.Activity{page_name}Binding
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class {page_name}Activity : AppCompatActivity() {{

    private lateinit var binding: Activity{page_name}Binding

    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        binding = Activity{page_name}Binding.inflate(layoutInflater)
        setContentView(binding.root)

        setupViews()
        loadData()
    }}

    private fun setupViews() {{
        supportActionBar?.apply {{
            title = "{page["name"]}"
            setDisplayHomeAsUpEnabled(true)
        }}

        // Setup UI components for {page["name"]}
        binding.pageTitle.text = "{page["name"]}"
        binding.pageDescription.text = "{page.get("description", "")}"
    }}

    private fun loadData() {{
        // Load data for {page["name"]}
    }}

    override fun onSupportNavigateUp(): Boolean {{
        onBackPressed()
        return true
    }}
}}
"""
            results[f"frontend/app/src/main/java/com/{package_name}/ui/activities/{page_name}Activity.kt"] = self._write_file(
                f"frontend/app/src/main/java/com/{package_name}/ui/activities/{page_name}Activity.kt",
                activity_content
            )
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created: {len(page_list)} Activity files[/#F1F5F9] ✓")

        # Create Layout XMLs
        # activity_main.xml
        activity_main_layout = f"""<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    xmlns:tools="http://schemas.android.com/tools"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    tools:context=".ui.activities.MainActivity">

    <TextView
        android:id="@+id/welcomeText"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Welcome to {project_name}"
        android:textSize="24sp"
        android:textStyle="bold"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toTopOf="parent" />

    <com.google.android.material.bottomnavigation.BottomNavigationView
        android:id="@+id/bottomNavigation"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        app:layout_constraintBottom_toBottomOf="parent"
        app:menu="@menu/bottom_nav_menu" />

</androidx.constraintlayout.widget.ConstraintLayout>
"""
        results["frontend/app/src/main/res/layout/activity_main.xml"] = self._write_file("frontend/app/src/main/res/layout/activity_main.xml", activity_main_layout)

        # activity_login.xml
        activity_login_layout = f"""<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:padding="24dp">

    <TextView
        android:id="@+id/titleText"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Welcome Back"
        android:textSize="28sp"
        android:textStyle="bold"
        android:layout_marginTop="80dp"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toTopOf="parent" />

    <TextView
        android:id="@+id/subtitleText"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Sign in to continue"
        android:textSize="16sp"
        android:layout_marginTop="8dp"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toBottomOf="@id/titleText" />

    <com.google.android.material.textfield.TextInputLayout
        android:id="@+id/emailLayout"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="48dp"
        style="@style/Widget.MaterialComponents.TextInputLayout.OutlinedBox"
        app:layout_constraintTop_toBottomOf="@id/subtitleText">

        <com.google.android.material.textfield.TextInputEditText
            android:id="@+id/emailInput"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:hint="Email"
            android:inputType="textEmailAddress" />

    </com.google.android.material.textfield.TextInputLayout>

    <com.google.android.material.textfield.TextInputLayout
        android:id="@+id/passwordLayout"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="16dp"
        style="@style/Widget.MaterialComponents.TextInputLayout.OutlinedBox"
        app:passwordToggleEnabled="true"
        app:layout_constraintTop_toBottomOf="@id/emailLayout">

        <com.google.android.material.textfield.TextInputEditText
            android:id="@+id/passwordInput"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:hint="Password"
            android:inputType="textPassword" />

    </com.google.android.material.textfield.TextInputLayout>

    <com.google.android.material.button.MaterialButton
        android:id="@+id/loginButton"
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:layout_marginTop="32dp"
        android:text="Sign In"
        android:textAllCaps="false"
        app:layout_constraintTop_toBottomOf="@id/passwordLayout" />

    <TextView
        android:id="@+id/registerLink"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_marginTop="16dp"
        android:text="Don't have an account? Sign Up"
        android:textColor="?attr/colorPrimary"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toBottomOf="@id/loginButton" />

</androidx.constraintlayout.widget.ConstraintLayout>
"""
        results["frontend/app/src/main/res/layout/activity_login.xml"] = self._write_file("frontend/app/src/main/res/layout/activity_login.xml", activity_login_layout)

        # activity_register.xml
        activity_register_layout = f"""<?xml version="1.0" encoding="utf-8"?>
<ScrollView
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <androidx.constraintlayout.widget.ConstraintLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:padding="24dp">

        <TextView
            android:id="@+id/titleText"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="Create Account"
            android:textSize="28sp"
            android:textStyle="bold"
            android:layout_marginTop="40dp"
            app:layout_constraintEnd_toEndOf="parent"
            app:layout_constraintStart_toStartOf="parent"
            app:layout_constraintTop_toTopOf="parent" />

        <com.google.android.material.textfield.TextInputLayout
            android:id="@+id/nameLayout"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="32dp"
            style="@style/Widget.MaterialComponents.TextInputLayout.OutlinedBox"
            app:layout_constraintTop_toBottomOf="@id/titleText">

            <com.google.android.material.textfield.TextInputEditText
                android:id="@+id/nameInput"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:hint="Full Name"
                android:inputType="textPersonName" />

        </com.google.android.material.textfield.TextInputLayout>

        <com.google.android.material.textfield.TextInputLayout
            android:id="@+id/emailLayout"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="16dp"
            style="@style/Widget.MaterialComponents.TextInputLayout.OutlinedBox"
            app:layout_constraintTop_toBottomOf="@id/nameLayout">

            <com.google.android.material.textfield.TextInputEditText
                android:id="@+id/emailInput"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:hint="Email"
                android:inputType="textEmailAddress" />

        </com.google.android.material.textfield.TextInputLayout>

        <com.google.android.material.textfield.TextInputLayout
            android:id="@+id/passwordLayout"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="16dp"
            style="@style/Widget.MaterialComponents.TextInputLayout.OutlinedBox"
            app:passwordToggleEnabled="true"
            app:layout_constraintTop_toBottomOf="@id/emailLayout">

            <com.google.android.material.textfield.TextInputEditText
                android:id="@+id/passwordInput"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:hint="Password"
                android:inputType="textPassword" />

        </com.google.android.material.textfield.TextInputLayout>

        <com.google.android.material.textfield.TextInputLayout
            android:id="@+id/confirmPasswordLayout"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="16dp"
            style="@style/Widget.MaterialComponents.TextInputLayout.OutlinedBox"
            app:passwordToggleEnabled="true"
            app:layout_constraintTop_toBottomOf="@id/passwordLayout">

            <com.google.android.material.textfield.TextInputEditText
                android:id="@+id/confirmPasswordInput"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:hint="Confirm Password"
                android:inputType="textPassword" />

        </com.google.android.material.textfield.TextInputLayout>

        <com.google.android.material.button.MaterialButton
            android:id="@+id/registerButton"
            android:layout_width="match_parent"
            android:layout_height="56dp"
            android:layout_marginTop="32dp"
            android:text="Create Account"
            android:textAllCaps="false"
            app:layout_constraintTop_toBottomOf="@id/confirmPasswordLayout" />

        <TextView
            android:id="@+id/loginLink"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginTop="16dp"
            android:layout_marginBottom="24dp"
            android:text="Already have an account? Sign In"
            android:textColor="?attr/colorPrimary"
            app:layout_constraintBottom_toBottomOf="parent"
            app:layout_constraintEnd_toEndOf="parent"
            app:layout_constraintStart_toStartOf="parent"
            app:layout_constraintTop_toBottomOf="@id/registerButton" />

    </androidx.constraintlayout.widget.ConstraintLayout>
</ScrollView>
"""
        results["frontend/app/src/main/res/layout/activity_register.xml"] = self._write_file("frontend/app/src/main/res/layout/activity_register.xml", activity_register_layout)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created: Layout XML files[/#F1F5F9] ✓")

        # Generate layout XMLs for each page
        for page in page_list:
            page_name = page["name"].replace(" ", "").replace("/", "")
            if page_name.lower() in ["login", "register", "main"]:
                continue

            layout_name = f"activity_{page_name.lower()}"
            layout_content = f"""<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:padding="16dp">

    <TextView
        android:id="@+id/pageTitle"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="{page["name"]}"
        android:textSize="24sp"
        android:textStyle="bold"
        android:layout_marginTop="16dp"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toTopOf="parent" />

    <TextView
        android:id="@+id/pageDescription"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="{page.get("description", "")}"
        android:textSize="16sp"
        android:layout_marginTop="8dp"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toBottomOf="@id/pageTitle" />

    <androidx.recyclerview.widget.RecyclerView
        android:id="@+id/contentList"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_marginTop="24dp"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintTop_toBottomOf="@id/pageDescription" />

</androidx.constraintlayout.widget.ConstraintLayout>
"""
            results[f"frontend/app/src/main/res/layout/{layout_name}.xml"] = self._write_file(
                f"frontend/app/src/main/res/layout/{layout_name}.xml",
                layout_content
            )

        # values/strings.xml
        strings_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{project_name}</string>
    <string name="login">Sign In</string>
    <string name="register">Create Account</string>
    <string name="logout">Logout</string>
    <string name="email">Email</string>
    <string name="password">Password</string>
    <string name="confirm_password">Confirm Password</string>
    <string name="name">Full Name</string>
</resources>
"""
        results["frontend/app/src/main/res/values/strings.xml"] = self._write_file("frontend/app/src/main/res/values/strings.xml", strings_xml)

        # values/colors.xml
        colors_xml = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="primary">#6200EE</color>
    <color name="primary_variant">#3700B3</color>
    <color name="secondary">#03DAC6</color>
    <color name="secondary_variant">#018786</color>
    <color name="background">#FFFFFF</color>
    <color name="surface">#FFFFFF</color>
    <color name="error">#B00020</color>
    <color name="on_primary">#FFFFFF</color>
    <color name="on_secondary">#000000</color>
    <color name="on_background">#000000</color>
    <color name="on_surface">#000000</color>
    <color name="on_error">#FFFFFF</color>
</resources>
"""
        results["frontend/app/src/main/res/values/colors.xml"] = self._write_file("frontend/app/src/main/res/values/colors.xml", colors_xml)

        # values/themes.xml
        themes_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.{project_name.replace(' ', '')}" parent="Theme.Material3.Light.NoActionBar">
        <item name="colorPrimary">@color/primary</item>
        <item name="colorPrimaryVariant">@color/primary_variant</item>
        <item name="colorSecondary">@color/secondary</item>
        <item name="android:statusBarColor">@color/primary</item>
    </style>
</resources>
"""
        results["frontend/app/src/main/res/values/themes.xml"] = self._write_file("frontend/app/src/main/res/values/themes.xml", themes_xml)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created: Resource files (strings, colors, themes)[/#F1F5F9] ✓")

        # Create menu for bottom navigation
        os.makedirs(os.path.join(self.project_dir, "frontend/app/src/main/res/menu"), exist_ok=True)
        bottom_nav_menu = """<?xml version="1.0" encoding="utf-8"?>
<menu xmlns:android="http://schemas.android.com/apk/res/android">
    <item
        android:id="@+id/nav_home"
        android:icon="@drawable/ic_home"
        android:title="Home" />
    <item
        android:id="@+id/nav_profile"
        android:icon="@drawable/ic_person"
        android:title="Profile" />
    <item
        android:id="@+id/nav_settings"
        android:icon="@drawable/ic_settings"
        android:title="Settings" />
</menu>
"""
        results["frontend/app/src/main/res/menu/bottom_nav_menu.xml"] = self._write_file("frontend/app/src/main/res/menu/bottom_nav_menu.xml", bottom_nav_menu)

        # Create xml folder for backup rules
        os.makedirs(os.path.join(self.project_dir, "frontend/app/src/main/res/xml"), exist_ok=True)

        backup_rules = """<?xml version="1.0" encoding="utf-8"?>
<full-backup-content>
</full-backup-content>
"""
        results["frontend/app/src/main/res/xml/backup_rules.xml"] = self._write_file("frontend/app/src/main/res/xml/backup_rules.xml", backup_rules)

        data_extraction_rules = """<?xml version="1.0" encoding="utf-8"?>
<data-extraction-rules>
    <cloud-backup></cloud-backup>
    <device-transfer></device-transfer>
</data-extraction-rules>
"""
        results["frontend/app/src/main/res/xml/data_extraction_rules.xml"] = self._write_file("frontend/app/src/main/res/xml/data_extraction_rules.xml", data_extraction_rules)

        # proguard-rules.pro
        proguard = """# Retrofit
-keepattributes Signature
-keepattributes *Annotation*
-keep class retrofit2.** { *; }
-keepclasseswithmembers class * {
    @retrofit2.http.* <methods>;
}

# Gson
-keep class com.google.gson.** { *; }
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer

# Keep data models
-keep class **.data.models.** { *; }
"""
        results["frontend/app/proguard-rules.pro"] = self._write_file("frontend/app/proguard-rules.pro", proguard)

        # README.md
        readme_content = f"""# {project_name} - Android App

## Overview
Android application built with Kotlin and Jetpack components.

## Tech Stack
- **Language**: Kotlin
- **Min SDK**: 24 (Android 7.0)
- **Target SDK**: 34 (Android 14)
- **Architecture**: MVVM with Repository pattern
- **DI**: Hilt
- **Networking**: Retrofit + OkHttp
- **Async**: Kotlin Coroutines

## Project Structure
```
app/
├── src/main/
│   ├── java/com/{package_name}/
│   │   ├── data/
│   │   │   ├── api/          # Retrofit API service
│   │   │   ├── models/       # Data models
│   │   │   └── repository/   # Data repositories
│   │   ├── ui/
│   │   │   ├── activities/   # Activity classes
│   │   │   ├── fragments/    # Fragment classes
│   │   │   └── adapters/     # RecyclerView adapters
│   │   └── utils/            # Utility classes
│   └── res/
│       ├── layout/           # XML layouts
│       ├── values/           # Colors, strings, themes
│       └── drawable/         # Icons and images
```

    ## Setup

1. Open project in Android Studio
2. Sync Gradle files
3. Update `BASE_URL` in `NetworkModule.kt` with your API URL
4. Build and run on emulator or device

## Features
{chr(10).join([f"- {p['name']}: {p.get('description', '')}" for p in page_list])}

## API Configuration
Update the API base URL in `data/api/NetworkModule.kt`:
```kotlin
private const val BASE_URL = "http://your-api-url/api/"
```

## Building
```bash
./gradlew assembleDebug
```

## Testing
```bash
./gradlew test
```

---
Generated by BOTUVIC
"""
        results["frontend/README.md"] = self._write_file("frontend/README.md", readme_content)

        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Kotlin Android frontend with {len(results)} files[/#F1F5F9] ✓")
        return results

    def _create_electron_frontend(self, design: Dict) -> Dict[str, bool]:
        """Create Electron desktop app."""
        results = {}
        from rich.console import Console
        console = Console()

        folders = [
        "frontend/src",
        "frontend/public"
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.project_dir, folder), exist_ok=True)

        package_json = """{
      "name": "frontend",
      "version": "1.0.0",
      "main": "main.js",
      "scripts": {
        "start": "electron .",
        "dev": "electron ."
      },
      "dependencies": {
        "electron": "^27.0.0"
      }
    }"""
        results["frontend/package.json"] = self._write_file("frontend/package.json", package_json)

        # main.js
        main_js = """const { app, BrowserWindow } = require('electron')
    const path = require('path')

    function createWindow() {
      const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
          nodeIntegration: true,
          contextIsolation: false
        }
      })

      win.loadFile('src/index.html')
    }

    app.whenReady().then(() => {
      createWindow()

      app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
          createWindow()
        }
      })
    })

    app.on('window-all-closed', () => {
      if (process.platform !== 'darwin') {
        app.quit()
      }
    })"""
        results["frontend/main.js"] = self._write_file("frontend/main.js", main_js)

        # src/index.html
        index_html = """<!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <title>Electron App</title>
        <style>
          body {
        font-family: Arial, sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        margin: 0;
        background: #f0f0f0;
          }
          .container {
        text-align: center;
          }
          h1 {
        font-size: 2rem;
        color: #333;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Welcome to Electron!</h1>
          <p>Desktop app built with Electron</p>
        </div>
      </body>
    </html>"""
        results["frontend/src/index.html"] = self._write_file("frontend/src/index.html", index_html)

        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created Electron desktop frontend[/#F1F5F9] ✓")
        return results

    def _generate_frontend_md_old(self, frontend_name: str, design: Dict) -> str:
        """OLD - Generate comprehensive frontend.md documentation."""
        content = f"""# Frontend Setup Guide

    ## Overview

    This frontend is built with **{frontend_name}**.

    ## Installation

    ```bash
    cd frontend
    npm install
    ```

    ## Running

    ```bash
    npm run dev
    ```

    Frontend will start at http://localhost:3000

    ## Project Structure

    ```
    frontend/
    ├── src/
    │   ├── components/  # Reusable components
    │   ├── pages/       # Page components
    │   ├── services/    # API services
    │   ├── hooks/       # Custom hooks
    │   └── utils/       # Utility functions
    ├── public/          # Static assets
    └── package.json
    ```

    ## Features

    - Authentication (Login/Register)
    - API integration
    - Routing
    - Tailwind CSS styling

    ## Environment Variables

    Copy `.env.example` to `.env`:

    ```bash
    cp .env.example .env
    ```

    Set your backend URL in `.env`:
    ```
    VITE_API_URL=http://localhost:8000
    ```

    ## Building for Production

    ```bash
    npm run build
    ```

    ---

    Built with BOTUVIC
    """
        return content
    
    def _generate_prd_md(self, project: Dict, profile: Dict) -> bool:
        """Generate Product Requirements Document (PRD)."""
        project_name = self._get_project_name(project)
        idea = project.get("idea", "")
        target_users = project.get("target_users", "")
        features = project.get("features", [])
        scale = project.get("scale", "medium")
        special_requirements = project.get("special_requirements", [])
        
        content = f"""# Product Requirements Document (PRD)
    # {project_name}

    Generated by BOTUVIC on {datetime.now().strftime("%Y-%m-%d %H:%M")}

    ---

    ## 1. Product Vision

    {idea}

    ## 2. Target Users

    {target_users}

    ## 3. Core Features

    """
        for i, feature in enumerate(features, 1):
            content += f"### Feature {i}: {feature}\n\n"
            content += f"**User Story**: As a user, I want to {feature.lower()} so that I can achieve my goals.\n\n"
            content += f"**Acceptance Criteria**:\n"
            content += f"- Feature is functional and tested\n"
            content += f"- User interface is intuitive\n"
            content += f"- Error handling is in place\n\n"

        content += f"""
    ## 4. Scale & Performance

    **Expected Scale**: {scale}

    """
        if scale == "small":
            content += "- Up to 1,000 users\n- Simple infrastructure\n- Basic optimization\n"
        elif scale == "medium":
            content += "- 1,000 - 100,000 users\n- Scalable architecture\n- Caching and optimization\n"
        else:
            content += "- 100,000+ users\n- Highly scalable infrastructure\n- Advanced optimization and CDN\n"

        content += """
    ## 5. Special Requirements

    """
        if special_requirements:
            for req in special_requirements:
                content += f"- {req}\n"
        else:
            content += "- None specified\n"

        content += """
    ## 6. Success Metrics

    - User adoption rate
    - Feature usage statistics
    - Performance benchmarks
    - User satisfaction scores

    ## 7. Risks & Mitigation

    **Technical Risks**:
    - Scalability challenges → Solution: Design for scale from start
    - Security vulnerabilities → Solution: Follow best practices, regular audits
    - Third-party API failures → Solution: Implement fallbacks and error handling

    **Business Risks**:
    - User adoption → Solution: Focus on UX and user feedback
    - Competition → Solution: Unique features and excellent execution

    ---

    **Note**: This PRD serves as the foundation. Read this first before starting development.
    """
        
        try:
            file_path = os.path.join(self.project_dir, "prd.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating prd.md: {e}")
            return False

    def _generate_database_md(self, project: Dict, db_schema: Dict) -> bool:
        """Generate detailed database documentation."""
        project_name = self._get_project_name(project)
        tech_stack = project.get("tech_stack", {})
        db_info = tech_stack.get("database", {})
        db_name = db_info.get("name", "Database") if isinstance(db_info, dict) else str(db_info)
        
        content = f"""# Database Documentation
    # {project_name} - {db_name}

    Generated by BOTUVIC on {datetime.now().strftime("%Y-%m-%d %H:%M")}

    ---

    ## Database Type

    **{db_name}**

    ## Schema Overview

    """
        
        tables = db_schema.get("tables", {})
        if tables:
            content += f"Total Tables: {len(tables)}\n\n"

            # Handle both list and dict formats
            if isinstance(tables, list):
                # List format: each item is a dict with "name" field
                for table in tables:
                    if isinstance(table, dict):
                        table_name = table.get("name", "unknown")
                        table_info = table
                    else:
                        table_name = str(table)
                        table_info = {}

                    content += f"### Table: `{table_name}`\n\n"
                    content += f"**Purpose**: {table_info.get('description', 'Main data storage for ' + table_name)}\n\n"

                    fields = table_info.get("fields", [])
                    if fields:
                        content += "**Fields**:\n\n"
                        content += "| Field | Type | Constraints | Description |\n"
                        content += "|-------|------|-------------|-------------|\n"

                        for field in fields:
                            field_name = field.get("name", "")
                            field_type = field.get("type", "")
                            constraints = field.get("constraints", "")
                            description = field.get("description", "")
                            content += f"| `{field_name}` | {field_type} | {constraints} | {description} |\n"

                        content += "\n"

                    relationships = table_info.get("relationships", [])
                    if relationships:
                        content += "**Relationships**:\n"
                        for rel in relationships:
                            content += f"- {rel}\n"
                        content += "\n"

                    indexes = table_info.get("indexes", [])
                    if indexes:
                        content += "**Indexes**:\n"
                        for idx in indexes:
                            if isinstance(idx, dict):
                                content += f"- {idx.get('name', 'index')} on {', '.join(idx.get('fields', []))}\n"
                            else:
                                content += f"- {idx}\n"
                        content += "\n"
            else:
                # Dict format: key is table name, value is table info
                for table_name, table_info in tables.items():
                    content += f"### Table: `{table_name}`\n\n"
                    content += f"**Purpose**: {table_info.get('description', 'Main data storage for ' + table_name)}\n\n"

                    fields = table_info.get("fields", [])
                    if fields:
                        content += "**Fields**:\n\n"
                        content += "| Field | Type | Constraints | Description |\n"
                        content += "|-------|------|-------------|-------------|\n"

                        for field in fields:
                            field_name = field.get("name", "")
                            field_type = field.get("type", "")
                            constraints = field.get("constraints", "")
                            description = field.get("description", "")
                            content += f"| `{field_name}` | {field_type} | {constraints} | {description} |\n"

                        content += "\n"

                    relationships = table_info.get("relationships", [])
                    if relationships:
                        content += "**Relationships**:\n"
                        for rel in relationships:
                            content += f"- {rel}\n"
                        content += "\n"

                    indexes = table_info.get("indexes", [])
                    if indexes:
                        content += "**Indexes**:\n"
                        for idx in indexes:
                            content += f"- {idx}\n"
                        content += "\n"

        content += """
    ## Data Operations

    ### Create Operations
    - User registration → Insert into `users` table
    - Content creation → Insert into content tables
    - Relationship creation → Insert into junction tables

    ### Read Operations
    - User login → Query `users` by email
    - Content listing → Query with pagination and filters
    - Relationships → JOIN queries for related data

    ### Update Operations
    - Profile updates → UPDATE `users` table
    - Content edits → UPDATE content tables
    - Status changes → UPDATE status fields

    ### Delete Operations
    - Soft delete preferred (set `deleted_at` timestamp)
    - Hard delete for GDPR compliance when requested
    - Cascade deletes for related data

    ## Performance Considerations

    ### Indexes
    """
        
        if tables:
            # Handle both list and dict formats
            if isinstance(tables, list):
                for table in tables:
                    if isinstance(table, dict):
                        table_name = table.get("name", "unknown")
                        table_info = table
                    else:
                        table_name = str(table)
                        table_info = {}
                    
                    indexes = table_info.get("indexes", [])
                    if indexes:
                        content += f"\n**{table_name}**:\n"
                        for idx in indexes:
                            if isinstance(idx, dict):
                                content += f"- {idx.get('name', 'index')} on {', '.join(idx.get('fields', []))}\n"
                            else:
                                content += f"- {idx}\n"
            else:
                # Dict format
            for table_name, table_info in tables.items():
                indexes = table_info.get("indexes", [])
                if indexes:
                    content += f"\n**{table_name}**:\n"
                    for idx in indexes:
                            if isinstance(idx, dict):
                                content += f"- {idx.get('name', 'index')} on {', '.join(idx.get('fields', []))}\n"
                            else:
                        content += f"- {idx}\n"

        content += """
    ### Query Optimization
    - Use prepared statements
    - Implement connection pooling
    - Cache frequently accessed data
    - Paginate large result sets

    ## Security

    ### Access Control
    - Row Level Security (RLS) policies
    - User can only access their own data
    - Admin roles for management operations

    ### Data Protection
    - Passwords hashed with bcrypt
    - Sensitive data encrypted at rest
    - SSL/TLS for data in transit

    ## Backup Strategy

    - Automated daily backups
    - Point-in-time recovery capability
    - Backup retention: 30 days
    - Test restore procedures monthly

    ## Migration Strategy

    1. Create migration files in `database/migrations/`
    2. Version each migration (001, 002, etc.)
    3. Test migrations on staging first
    4. Run migrations during low-traffic windows
    5. Keep rollback scripts ready

    ---

    **Note**: This document defines the complete database structure. Refer to this when implementing any database operations.
    """
        
        try:
            file_path = os.path.join(self.project_dir, "database.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating database.md: {e}")
            return False

    def _generate_backend_md_v2(self, project: Dict, backend_arch: Dict, db_schema: Dict) -> bool:
        """Generate detailed backend documentation with clean architecture flow."""
        project_name = self._get_project_name(project)
        tech_stack = project.get("tech_stack", {})
        backend_info = tech_stack.get("backend", {})
        backend_name = backend_info.get("name", "Backend") if isinstance(backend_info, dict) else str(backend_info)
        
        content = f"""# Backend Documentation
    # {project_name} - {backend_name}

    Generated by BOTUVIC on {datetime.now().strftime("%Y-%m-%d %H:%M")}

    ---

    ## Architecture Overview

    **Framework**: {backend_name}

    ### Clean Architecture Flow

    ```
    Request → Router → Controller → Service → Repository → Database
                      ↓
    Response ← Controller ← Service ← Repository ← Database
    ```

    ### Folder Structure

    ```
    backend/
    ├── src/
    │   ├── routes/          # API endpoint definitions
    │   ├── controllers/     # Request handling & validation
    │   ├── services/        # Business logic
    │   ├── repositories/    # Database operations
    │   ├── middleware/      # Auth, logging, error handling
    │   ├── models/          # Data models & types
    │   ├── utils/           # Helper functions
    │   └── config/          # Configuration files
    ├── tests/              # Test files
    ├── .env                # Environment variables
    └── server.js/main.py   # Application entry point
    ```

    ## API Endpoints

    """
        
        endpoints = backend_arch.get("endpoints", [])
        if endpoints:
            # Group endpoints by resource
            grouped = {}
            for endpoint in endpoints:
                method = endpoint.get("method", "GET")
                path = endpoint.get("path", "/")
                resource = path.split('/')[1] if '/' in path else "general"
            
                if resource not in grouped:
                    grouped[resource] = []
                grouped[resource].append(endpoint)
        
            for resource, resource_endpoints in grouped.items():
                content += f"### {resource.title()} Endpoints\n\n"
            
                for endpoint in resource_endpoints:
                    method = endpoint.get("method", "GET")
                    path = endpoint.get("path", "/")
                    description = endpoint.get("description", "")
                    auth_required = endpoint.get("auth_required", False)
                
                    content += f"#### `{method} {path}`\n\n"
                    content += f"**Description**: {description}\n\n"
                    content += f"**Authentication**: {'Required' if auth_required else 'Not required'}\n\n"
                
                    # Request body
                    request_body = endpoint.get("request_body", {})
                    if request_body:
                        content += "**Request Body**:\n```json\n"
                        content += json.dumps(request_body, indent=2)
                        content += "\n```\n\n"
                
                    # Response
                    response = endpoint.get("response", {})
                    if response:
                        content += "**Response**:\n```json\n"
                        content += json.dumps(response, indent=2)
                        content += "\n```\n\n"
                
                    # Implementation flow
                    content += f"**Implementation Flow**:\n"
                    content += f"1. Route (`routes/{resource}.js`) receives request\n"
                    content += f"2. Controller (`controllers/{resource}Controller.js`) validates input\n"
                    content += f"3. Service (`services/{resource}Service.js`) executes business logic\n"
                    content += f"4. Repository (`repositories/{resource}Repository.js`) performs database operations\n"
                    content += f"5. Response sent back through controller\n\n"
                
                    # Database operations
                    db_operations = endpoint.get("database_operations", [])
                    if db_operations:
                        content += "**Database Operations**:\n"
                        for op in db_operations:
                            content += f"- {op}\n"
                        content += "\n"
                
                    content += "---\n\n"

        content += """
    ## Authentication Flow

    ### Sign Up
    1. User submits email/password
    2. Validate email format and password strength
    3. Hash password with bcrypt (salt rounds: 10)
    4. Create user record in database
    5. Generate JWT token
    6. Return token + user data

    ### Login
    1. User submits email/password
    2. Query user by email
    3. Compare password with bcrypt
    4. If valid, generate JWT token
    5. Return token + user data

    ### Protected Routes
    1. Extract token from Authorization header
    2. Verify JWT token
    3. Decode user ID from token
    4. Attach user to request object
    5. Continue to route handler

    ## Business Logic

    ### Service Layer Responsibilities
    - Input validation (business rules)
    - Complex calculations
    - External API calls
    - Transaction management
    - Error handling

    ### Example Service Method
    ```javascript
    async createPost(userId, postData) {
      // Validate user exists
      const user = await this.userRepo.findById(userId);
      if (!user) throw new Error('User not found');
  
      // Validate post data
      if (!postData.content || postData.content.length > 500) {
        throw new Error('Invalid content length');
      }
  
      // Create post
      const post = await this.postRepo.create({
        userId,
        content: postData.content,
        createdAt: new Date()
      });
  
      // Update user stats
      await this.userRepo.incrementPostCount(userId);
  
      return post;
    }
    ```

    ## Error Handling

    ### Error Types
    - Validation errors (400)
    - Authentication errors (401)
    - Authorization errors (403)
    - Not found errors (404)
    - Server errors (500)

    ### Error Response Format
    ```json
    {
      "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
          "field": "email",
          "issue": "Invalid email format"
        }
      }
    }
    ```

    ## Middleware

    ### Authentication Middleware
    - Verifies JWT token
    - Attaches user to request
    - Returns 401 if invalid

    ### Logging Middleware
    - Logs all requests
    - Includes timestamp, method, path, status
    - Logs response time

    ### Error Handling Middleware
    - Catches all errors
    - Formats error response
    - Logs error details

    ## File-by-File Breakdown

    ### `server.js` / `main.py`
    - Initialize app
    - Setup middleware
    - Register routes
    - Start server
    - Handle graceful shutdown

    ### `routes/{resource}.js`
    - Define all endpoints for resource
    - Map to controller methods
    - Apply middleware (auth, validation)

    ### `controllers/{resource}Controller.js`
    - Extract request data
    - Call service methods
    - Format responses
    - Handle controller-level errors

    ### `services/{resource}Service.js`
    - Implement business logic
    - Coordinate multiple repositories
    - Handle transactions
    - Validate business rules

    ### `repositories/{resource}Repository.js`
    - Direct database operations
    - CRUD methods
    - Query building
    - Data mapping

    ## Testing Strategy

    ### Unit Tests
    - Test services in isolation
    - Mock repositories
    - Test business logic

    ### Integration Tests
    - Test API endpoints
    - Use test database
    - Test full request/response cycle

    ### Test Coverage Goals
    - Services: 90%+
    - Controllers: 80%+
    - Repositories: 80%+

    ---

    **Note**: This document contains the complete backend architecture. Follow this structure when implementing features.
    """
        
        try:
            file_path = os.path.join(self.project_dir, "backend.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating backend.md: {e}")
            return False

    def _generate_frontend_md(self, project: Dict, frontend_design: Dict, backend_arch: Dict) -> bool:
        """Generate detailed frontend documentation with UI/UX specifications."""
        project_name = self._get_project_name(project)
        tech_stack = project.get("tech_stack", {})
        frontend_info = tech_stack.get("frontend", {})
        frontend_name = frontend_info.get("name", "Frontend") if isinstance(frontend_info, dict) else str(frontend_info)
        
        content = f"""# Frontend Documentation
    # {project_name} - {frontend_name}

    Generated by BOTUVIC on {datetime.now().strftime("%Y-%m-%d %H:%M")}

    ---

    ## Architecture Overview

    **Framework**: {frontend_name}

    ### Folder Structure

    ```
    frontend/
    ├── src/
    │   ├── components/       # Reusable UI components
    │   │   ├── ui/          # Base components (Button, Input, Card)
    │   │   ├── layout/      # Layout components (Header, Footer, Sidebar)
    │   │   └── features/    # Feature-specific components
    │   ├── pages/           # Page components (routes)
    │   ├── hooks/           # Custom React hooks
    │   ├── services/        # API service layer
    │   ├── store/           # State management
    │   ├── utils/           # Helper functions
    │   ├── styles/          # Global styles
    │   └── assets/          # Images, fonts, icons
    ├── public/              # Static assets
    └── package.json
    ```

    ## Design System

    ### Color Palette

    **Primary Colors**:
    - Primary: #3B82F6 (Blue)
    - Secondary: #8B5CF6 (Purple)
    - Accent: #10B981 (Green)

    **Neutral Colors**:
    - Background: #FFFFFF (White)
    - Surface: #F9FAFB (Light Gray)
    - Border: #E5E7EB (Gray)
    - Text Primary: #111827 (Dark Gray)
    - Text Secondary: #6B7280 (Medium Gray)

    **Status Colors**:
    - Success: #10B981 (Green)
    - Warning: #F59E0B (Orange)
    - Error: #EF4444 (Red)
    - Info: #3B82F6 (Blue)

    ### Typography

    **Font Family**: Inter, system-ui, sans-serif

    **Font Sizes**:
    - Heading 1: 2.5rem (40px)
    - Heading 2: 2rem (32px)
    - Heading 3: 1.5rem (24px)
    - Body: 1rem (16px)
    - Small: 0.875rem (14px)
    - Tiny: 0.75rem (12px)

    **Font Weights**:
    - Regular: 400
    - Medium: 500
    - Semibold: 600
    - Bold: 700

    ### Spacing System

    - xs: 4px
    - sm: 8px
    - md: 16px
    - lg: 24px
    - xl: 32px
    - 2xl: 48px
    - 3xl: 64px

    ### Component Specifications

    #### Button
    - Height: 40px (default), 32px (small), 48px (large)
    - Padding: 12px 24px (default)
    - Border radius: 8px
    - Font weight: 500
    - Variants: primary, secondary, outline, ghost, danger

    #### Input
    - Height: 40px
    - Padding: 10px 12px
    - Border: 1px solid #E5E7EB
    - Border radius: 8px
    - Focus: Blue border + shadow

    #### Card
    - Background: White
    - Border: 1px solid #E5E7EB
    - Border radius: 12px
    - Padding: 24px
    - Shadow: 0 1px 3px rgba(0,0,0,0.1)

    ## Pages & User Flows

    """
        
        pages = frontend_design.get("pages", [])
        if pages:
            for page in pages:
                # Handle both string and dict formats
                if isinstance(page, dict):
                page_name = page.get("name", "Page")
                route = page.get("route", "/")
                description = page.get("description", "")
                components = page.get("components", [])
                user_flow = page.get("user_flow", [])
                else:
                    # Page is a string
                    page_name = str(page)
                    route = f"/{page_name.lower().replace(' ', '-')}"
                    description = f"{page_name} page"
                    components = []
                    user_flow = []
            
                content += f"### {page_name}\n\n"
                content += f"**Route**: `{route}`\n\n"
                content += f"**Description**: {description}\n\n"
            
                if components:
                    content += "**Components Needed**:\n"
                    for comp in components:
                        content += f"- {comp}\n"
                    content += "\n"
            
                content += "**Layout**:\n"
                content += f"```\n"
                content += f"+------------------------------------------+\n"
                content += f"|              Header/Navbar               |\n"
                content += f"+------------------------------------------+\n"
                content += f"|                                          |\n"
                content += f"|           Main Content Area              |\n"
                content += f"|                                          |\n"
                content += f"+------------------------------------------+\n"
                content += f"```\n\n"
            
                if user_flow:
                    content += "**User Flow**:\n"
                    for i, step in enumerate(user_flow, 1):
                        content += f"{i}. {step}\n"
                    content += "\n"
            
                content += "**State Management**:\n"
                content += f"- Loading state (show skeleton/spinner)\n"
                content += f"- Error state (show error message)\n"
                content += f"- Empty state (show empty message)\n"
                content += f"- Success state (show content)\n\n"
            
                content += "---\n\n"

        content += """
    ## Component Library

    ### UI Components (src/components/ui/)

    #### Button Component
    ```jsx
    <Button 
      variant="primary|secondary|outline|ghost"
      size="small|default|large"
      onClick={handleClick}
      disabled={false}
    >
      Click Me
    </Button>
    ```

    #### Input Component
    ```jsx
    <Input
      type="text|email|password|number"
      placeholder="Enter text..."
      value={value}
      onChange={handleChange}
      error={errorMessage}
    />
    ```

    #### Card Component
    ```jsx
    <Card>
      <Card.Header>Title</Card.Header>
      <Card.Body>Content</Card.Body>
      <Card.Footer>Actions</Card.Footer>
    </Card>
    ```

    ### Layout Components (src/components/layout/)

    #### Header
    - Logo on left
    - Navigation links in center
    - User menu on right
    - Responsive (hamburger menu on mobile)

    #### Sidebar
    - Collapsible on desktop
    - Drawer on mobile
    - Navigation links
    - User profile section

    #### Footer
    - Links to pages
    - Social media icons
    - Copyright information

    ## State Management

    ### Global State
    - User authentication state
    - User profile data
    - Theme preference (light/dark)
    - Notifications

    ### Local State
    - Form inputs
    - UI state (modals, dropdowns)
    - Pagination
    - Filters & sorting

    ## API Integration

    ### API Service Structure
    ```javascript
    // src/services/api.js
    const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';

    export const api = {
      // Auth
      login: (email, password) => post('/auth/login', { email, password }),
      signup: (data) => post('/auth/signup', data),
  
      // Users
      getProfile: () => get('/users/me'),
      updateProfile: (data) => put('/users/me', data),
  
      // Posts
      getPosts: () => get('/posts'),
      createPost: (data) => post('/posts', data),
    };
    ```

    ### API Call Pattern
    ```javascript
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [data, setData] = useState(null);

    const fetchData = async () => {
      setLoading(true);
      setError(null);
  
      try {
        const result = await api.getPosts();
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    ```

    ## Responsive Design

    ### Breakpoints
    - Mobile: < 640px
    - Tablet: 640px - 1024px
    - Desktop: > 1024px

    ### Mobile-First Approach
    1. Design for mobile first
    2. Add tablet styles with media queries
    3. Add desktop styles with media queries

    ### Example
    ```css
    /* Mobile (default) */
    .container {
      padding: 16px;
    }

    /* Tablet */
    @media (min-width: 640px) {
      .container {
        padding: 24px;
      }
    }

    /* Desktop */
    @media (min-width: 1024px) {
      .container {
        padding: 32px;
        max-width: 1200px;
        margin: 0 auto;
      }
    }
    ```

    ## Performance Optimization

    ### Code Splitting
    - Route-based code splitting
    - Lazy load heavy components
    - Dynamic imports for large libraries

    ### Image Optimization
    - Use WebP format when possible
    - Lazy load images below the fold
    - Use appropriate sizes (responsive images)
    - Compress images before upload

    ### Caching Strategy
    - Cache API responses (with invalidation)
    - Use React Query or SWR for data fetching
    - Service worker for offline support

    ## Accessibility

    ### Requirements
    - Semantic HTML elements
    - ARIA labels for interactive elements
    - Keyboard navigation support
    - Focus indicators
    - Color contrast ratios (WCAG AA)
    - Screen reader testing

    ### Example
    ```jsx
    <button
      aria-label="Close modal"
      onClick={closeModal}
      className="close-button"
    >
      <CloseIcon aria-hidden="true" />
    </button>
    ```

    ## Testing Strategy

    ### Unit Tests
    - Test components in isolation
    - Test custom hooks
    - Test utility functions

    ### Integration Tests
    - Test user flows
    - Test API integration
    - Test state management

    ### E2E Tests
    - Test critical user journeys
    - Test across browsers
    - Test responsive behavior

    ---

    **Note**: This document defines the complete frontend structure. Follow these specifications when building UI components.
    """
        
        try:
            file_path = os.path.join(self.project_dir, "frontend.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating frontend.md: {e}")
            return False

    def _generate_test_plan_md(self, project: Dict, roadmap: Dict) -> bool:
        """Generate comprehensive test plan."""
        project_name = self._get_project_name(project)
        
        content = f"""# Test Plan
    # {project_name}

    Generated by BOTUVIC on {datetime.now().strftime("%Y-%m-%d %H:%M")}

    ---

    ## Testing Strategy

    ### Test Levels
    1. **Unit Tests** - Individual functions/components
    2. **Integration Tests** - API endpoints and flows
    3. **E2E Tests** - Complete user journeys
    4. **Manual Tests** - Exploratory testing

    ## Unit Testing

    ### Backend Unit Tests

    #### Authentication Service
    - [ ] Password hashing works correctly
    - [ ] JWT token generation is valid
    - [ ] Token verification works
    - [ ] Invalid tokens are rejected

    #### User Service
    - [ ] User creation validates input
    - [ ] Email uniqueness is enforced
    - [ ] User updates work correctly
    - [ ] User deletion cascades properly

    ### Frontend Unit Tests

    #### Components
    - [ ] Button renders with correct props
    - [ ] Input handles onChange correctly
    - [ ] Form validation works
    - [ ] Error messages display properly

    #### Hooks
    - [ ] useAuth returns correct auth state
    - [ ] useFetch handles loading/error states
    - [ ] Custom hooks trigger re-renders

    ## Integration Testing

    ### API Endpoint Tests

    #### Authentication Endpoints
    - [ ] POST /auth/signup creates user
      - Valid data returns 201 + token
      - Duplicate email returns 409
      - Invalid email returns 400
      - Weak password returns 400

    - [ ] POST /auth/login authenticates user
      - Valid credentials return 200 + token
      - Invalid credentials return 401
      - Missing fields return 400

    #### Protected Endpoints
    - [ ] GET /users/me returns user data
      - With valid token returns 200 + data
      - Without token returns 401
      - With invalid token returns 401

    ### Database Integration
    - [ ] Transactions rollback on error
    - [ ] Foreign key constraints work
    - [ ] Cascade deletes work
    - [ ] Indexes improve query performance

    ## End-to-End Testing

    ### Critical User Journeys

    #### Journey 1: New User Registration
    1. [ ] User visits signup page
    2. [ ] User fills in registration form
    3. [ ] User submits form
    4. [ ] Account is created
    5. [ ] User is redirected to dashboard
    6. [ ] Welcome message is shown

    **Expected Result**: User can register and access dashboard

    #### Journey 2: User Login
    1. [ ] User visits login page
    2. [ ] User enters credentials
    3. [ ] User clicks login
    4. [ ] User is authenticated
    5. [ ] User sees their dashboard

    **Expected Result**: User can login successfully

    #### Journey 3: Create Content
    1. [ ] User is logged in
    2. [ ] User navigates to create page
    3. [ ] User fills in content form
    4. [ ] User submits content
    5. [ ] Content appears in feed
    6. [ ] Success message shown

    **Expected Result**: User can create and view content

    ## Performance Testing

    ### Load Testing
    - [ ] API handles 100 concurrent requests
    - [ ] Database queries under 100ms
    - [ ] Page load time under 2 seconds
    - [ ] API response time under 500ms

    ### Stress Testing
    - [ ] System handles peak load
    - [ ] Graceful degradation under stress
    - [ ] Error handling under load

    ## Security Testing

    ### Authentication & Authorization
    - [ ] Cannot access protected routes without auth
    - [ ] Cannot access other users' private data
    - [ ] XSS attacks are prevented
    - [ ] CSRF protection works
    - [ ] SQL injection is prevented

    ### Data Protection
    - [ ] Passwords are hashed
    - [ ] Sensitive data is encrypted
    - [ ] API keys are not exposed
    - [ ] HTTPS is enforced

    ## Browser Compatibility

    ### Desktop Browsers
    - [ ] Chrome (latest)
    - [ ] Firefox (latest)
    - [ ] Safari (latest)
    - [ ] Edge (latest)

    ### Mobile Browsers
    - [ ] iOS Safari
    - [ ] Chrome Mobile
    - [ ] Firefox Mobile

    ## Accessibility Testing

    - [ ] Keyboard navigation works
    - [ ] Screen reader compatibility
    - [ ] Color contrast ratios meet WCAG AA
    - [ ] Focus indicators are visible
    - [ ] ARIA labels are present

    ## Phase-Based Testing

    """
        
        phases = roadmap.get("phases", [])
        for phase in phases:
            phase_num = phase.get("phase_number", 1)
            phase_name = phase.get("name", "Phase")
        
            content += f"### Phase {phase_num}: {phase_name}\n\n"
            content += f"**Test Checklist**:\n"
            content += f"- [ ] All features from this phase work\n"
            content += f"- [ ] No regression in previous phases\n"
            content += f"- [ ] Error handling works\n"
            content += f"- [ ] Performance is acceptable\n"
            content += f"- [ ] Code is documented\n\n"
            content += f"**Acceptance Criteria**:\n"
        
            tasks = phase.get("tasks", [])
            for task in tasks:
                task_name = task.get("name", "Task")
                content += f"- [ ] {task_name} is complete and tested\n"
        
            content += "\n---\n\n"

        content += """
    ## Bug Tracking

    ### Bug Report Template
    ```
    **Title**: Brief description

    **Severity**: Critical / High / Medium / Low

    **Steps to Reproduce**:
    1. Step one
    2. Step two
    3. Step three

    **Expected Result**: What should happen

    **Actual Result**: What actually happened

    **Environment**: Browser, OS, device

    **Screenshots**: If applicable
    ```

    ## Testing Tools

    ### Backend
    - Unit: Jest / Pytest
    - Integration: Supertest / Pytest
    - API: Postman / Insomnia

    ### Frontend
    - Unit: Jest + React Testing Library
    - E2E: Cypress / Playwright
    - Visual: Storybook

    ## Test Execution Schedule

    ### During Development
    - Run unit tests on every code change
    - Run integration tests before commit
    - Run E2E tests before PR merge

    ### Pre-Release
    - Full test suite execution
    - Manual testing of all features
    - Performance testing
    - Security audit

    ### Post-Release
    - Smoke tests in production
    - Monitor error logs
    - User acceptance testing

    ---

    **Note**: Update this test plan as new features are added. Check off tests as they pass.
    """
        
        try:
            file_path = os.path.join(self.project_dir, "test-plan.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating test-plan.md: {e}")
            return False

    def _generate_progress_tracker_md(self, project: Dict) -> bool:
        """Generate progress tracking document."""
        project_name = self._get_project_name(project)
        
        content = f"""# Progress Tracker
    # {project_name}

    Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

    ---

    ## Current Status

    **Overall Progress**: 0%

    **Current Phase**: Not Started

    **Last Activity**: Project initialized

    ---

    ## Phase Completion Status

    ### Phase 1: Foundation & Setup
    - **Status**: ⏸️ Not Started
    - **Progress**: 0/X tasks
    - **Started**: N/A
    - **Completed**: N/A
    - **Notes**: Waiting to begin

    ### Phase 2: Backend Development
    - **Status**: ⏸️ Not Started
    - **Progress**: 0/X tasks
    - **Started**: N/A
    - **Completed**: N/A
    - **Notes**: Waiting for Phase 1

    ### Phase 3: Frontend Development
    - **Status**: ⏸️ Not Started
    - **Progress**: 0/X tasks
    - **Started**: N/A
    - **Completed**: N/A
    - **Notes**: Waiting for Phase 2

    ### Phase 4: Feature Implementation
    - **Status**: ⏸️ Not Started
    - **Progress**: 0/X tasks
    - **Started**: N/A
    - **Completed**: N/A
    - **Notes**: Waiting for Phase 3

    ### Phase 5: Testing & Polish
    - **Status**: ⏸️ Not Started
    - **Progress**: 0/X tasks
    - **Started**: N/A
    - **Completed**: N/A
    - **Notes**: Waiting for Phase 4

    ### Phase 6: Deployment
    - **Status**: ⏸️ Not Started
    - **Progress**: 0/X tasks
    - **Started**: N/A
    - **Completed**: N/A
    - **Notes**: Waiting for Phase 5

    ---

    ## Code Review Results

    ### Phase 1 Review
    - **Status**: Pending
    - **Issues Found**: 0
    - **Feedback**: Not yet reviewed

    ---

    ## Blockers & Issues

    ### Current Blockers
    - None

    ### Resolved Issues
    - None yet

    ---

    ## Next Steps

    1. Begin Phase 1: Foundation & Setup
    2. Complete database setup
    3. Set up authentication
    4. Create basic API structure

    ---

    ## Metrics

    ### Code Quality
    - **Test Coverage**: 0%
    - **Linting Errors**: 0
    - **Code Review Score**: N/A

    ### Performance
    - **API Response Time**: N/A
    - **Page Load Time**: N/A
    - **Lighthouse Score**: N/A

    ---

    **Note**: This file is automatically updated by BOTUVIC as you complete phases. Check task.md for detailed task tracking.
    """
        
        try:
            file_path = os.path.join(self.project_dir, "progress-tracker.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating progress-tracker.md: {e}")
            return False

    def _generate_ai_instructions(self, project: Dict, db_schema: Dict, backend_arch: Dict, 
                                   frontend_design: Dict, roadmap: Dict, ai_tool_name: str) -> bool:
        """Generate generic AI instructions that work with any AI tool."""
        project_name = self._get_project_name(project)
        
        content = f"""# AI Development Instructions
    # {project_name} - {ai_tool_name}

    Generated by BOTUVIC on {datetime.now().strftime("%Y-%m-%d %H:%M")}

    ---

    ## System Prompt for AI

    You are an expert full-stack developer tasked with building {project_name}. You have deep expertise in the technologies used in this project and follow best practices for clean, maintainable code.

    **Your Responsibilities**:
    - Write production-quality code
    - Follow the architecture defined in documentation
    - Implement proper error handling
    - Add necessary comments and documentation
    - Write tests for your code
    - Ensure security best practices

    **Your Approach**:
    - Read documentation thoroughly before coding
    - Follow established patterns in the codebase
    - Ask clarifying questions when requirements are unclear
    - Test your code before marking tasks complete
    - Keep code DRY (Don't Repeat Yourself)

    ---

    ## Reading Order

    Before starting development, read these documents in order:

    1. **`prd.md`** - Understand the product vision and requirements
    2. **`database.md`** - Understand the data structure
    3. **`backend.md`** - Understand the API architecture
    4. **`frontend.md`** - Understand the UI/UX requirements
    5. **`plan.md`** - See the complete project plan
    6. **`task.md`** - See the task breakdown
    7. **`test-plan.md`** - Understand testing requirements

    ---

    ## Development Workflow

    ### Step 1: Understand the Task
    - Read the task description in `task.md`
    - Identify which files need to be created/modified
    - Check `backend.md` or `frontend.md` for specifications
    - Review `database.md` for data operations

    ### Step 2: Plan Implementation
    - Identify components/modules needed
    - Plan the code structure
    - Consider edge cases and error handling
    - Think about testing approach

    ### Step 3: Implement
    - Write clean, readable code
    - Follow the architecture patterns
    - Add proper error handling
    - Include comments for complex logic

    ### Step 4: Test
    - Write unit tests
    - Test manually
    - Check error cases
    - Verify against acceptance criteria

    ### Step 5: Update Progress
    - Check off the task in `task.md`
    - Update `progress-tracker.md` if phase complete
    - Document any issues or decisions made

    ---

    ## Phase-by-Phase Instructions

    """
        
        phases = roadmap.get("phases", [])
        for phase in phases:
            phase_num = phase.get("phase_number", 1)
            phase_name = phase.get("name", "Phase")
            phase_desc = phase.get("description", "")
            estimated_days = phase.get("estimated_days", 0)
        
            content += f"### Phase {phase_num}: {phase_name}\n\n"
            content += f"**Description**: {phase_desc}\n\n"
            content += f"**Estimated Time**: {estimated_days} days\n\n"
            content += f"**What to Build**:\n\n"
        
            tasks = phase.get("tasks", [])
            for task in tasks:
                task_num = task.get("task_number", 1)
                task_name = task.get("name", "Task")
                objective = task.get("objective", "")
                files = task.get("files", [])
                acceptance = task.get("acceptance_criteria", "")
            
                content += f"#### Task {phase_num}.{task_num}: {task_name}\n\n"
                content += f"**Objective**: {objective}\n\n"
            
                if files:
                    content += "**Files to Create/Modify**:\n"
                    for file in files:
                        content += f"- `{file}`\n"
                    content += "\n"
            
                content += f"**Acceptance Criteria**: {acceptance}\n\n"
                content += f"**Implementation Notes**:\n"
                content += f"- Refer to `backend.md` or `frontend.md` for detailed specifications\n"
                content += f"- Check `database.md` for data operations\n"
                content += f"- Follow the clean architecture pattern\n"
                content += f"- Add error handling and validation\n"
                content += f"- Write tests (see `test-plan.md`)\n\n"
                content += "---\n\n"
        
            content += f"**Phase {phase_num} Testing**:\n"
            content += f"- Run all tests for this phase\n"
            content += f"- Manually test all features\n"
            content += f"- Verify no regressions in previous phases\n"
            content += f"- Check off phase in `progress-tracker.md`\n\n"
            content += "---\n\n"

        content += f"""
    ## Coding Standards

    ### Code Style
    - Use consistent indentation (2 or 4 spaces)
    - Follow naming conventions for the language
    - Keep functions small and focused
    - Use meaningful variable names

    ### Error Handling
    ```javascript
    try {{
      // Your code here
    }} catch (error) {{
      console.error('Operation failed:', error);
      throw new Error('User-friendly error message');
    }}
    ```

    ### Comments
    - Add comments for complex logic
    - Document function parameters and return values
    - Explain "why" not "what" (code shows what)

    ### Testing
    - Write tests alongside code
    - Test happy path and error cases
    - Aim for high test coverage

    ---

    ## Common Patterns

    ### API Call Pattern (Frontend)
    ```javascript
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchData = async () => {{
      setLoading(true);
      try {{
        const data = await api.getData();
        setData(data);
      }} catch (err) {{
        setError(err.message);
      }} finally {{
        setLoading(false);
      }}
    }};
    ```

    ### Service Method Pattern (Backend)
    ```javascript
    async function createResource(userId, data) {{
      // 1. Validate input
      if (!data.required_field) {{
        throw new ValidationError('Required field missing');
      }}
  
      // 2. Check permissions
      const user = await userRepo.findById(userId);
      if (!user) throw new UnauthorizedError();
  
      // 3. Perform operation
      const resource = await resourceRepo.create({{
        ...data,
        userId,
        createdAt: new Date()
      }});
  
      // 4. Return result
      return resource;
    }}
    ```

    ---

    ## When You Get Stuck

    1. **Review Documentation**: Re-read relevant sections
    2. **Check Existing Code**: Look for similar patterns
    3. **Search Online**: Look for best practices
    4. **Ask for Clarification**: Note unclear requirements
    5. **Start Simple**: Build MVP first, then enhance

    ---

    ## Tips for {ai_tool_name}

    ### Effective Prompts
    - Be specific about what you need
    - Include context from documentation
    - Mention the file you're working on
    - Ask for explanations if needed

    ### Example Prompts
    - "Implement the createPost function in backend/services/postService.js according to backend.md specifications"
    - "Create the Login component following the design in frontend.md, with proper error handling"
    - "Add unit tests for the authentication service"

    ### If Output is Incomplete
    - Say "continue" to get more
    - Or "continue from line X"

    ---

    **Remember**: Quality over speed. Write code you'd be proud to maintain. Check off tasks in `task.md` as you complete them.
    """
        
        try:
            file_path = os.path.join(self.project_dir, f"{ai_tool_name.lower()}.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating {ai_tool_name}.md: {e}")
            return False

    def _generate_team_member_file(self, project: Dict, member: Dict, db_schema: Dict, 
                                    backend_arch: Dict, frontend_design: Dict, roadmap: Dict) -> bool:
        """Generate task file for specific team member."""
        project_name = self._get_project_name(project)
        member_name = member.get("name", "Team Member")
        member_role = member.get("role", "Developer")
        member_focus = member.get("focus", "")
        
        content = f"""# Team Member Tasks
    # {project_name} - {member_name} ({member_role})

    Generated by BOTUVIC on {datetime.now().strftime("%Y-%m-%d %H:%M")}

    ---

    ## Your Role

    **Name**: {member_name}
    **Role**: {member_role}
    **Focus Area**: {member_focus}

    ---

    ## Documents to Read

    Based on your role, prioritize these documents:

    """
        
        if "backend" in member_role.lower() or "api" in member_focus.lower():
            content += """
    1. **`prd.md`** - Product requirements
    2. **`database.md`** - Database structure (CRITICAL for you)
    3. **`backend.md`** - Your main reference (CRITICAL)
    4. **`plan.md`** - Overall plan
    5. **`task.md`** - Task breakdown
    6. **`test-plan.md`** - Testing requirements

    """
        elif "frontend" in member_role.lower() or "ui" in member_focus.lower():
            content += """
    1. **`prd.md`** - Product requirements
    2. **`frontend.md`** - Your main reference (CRITICAL)
    3. **`backend.md`** - API endpoints you'll call
    4. **`plan.md`** - Overall plan
    5. **`task.md`** - Task breakdown
    6. **`test-plan.md`** - Testing requirements

    """
        else:
            content += """
    1. **`prd.md`** - Product requirements
    2. **`plan.md`** - Overall plan
    3. **`database.md`** - Database structure
    4. **`backend.md`** - Backend API
    5. **`frontend.md`** - Frontend UI
    6. **`task.md`** - Task breakdown
    7. **`test-plan.md`** - Testing requirements

    """

        content += f"""
    ---

    ## Your Tasks

    """
        
        phases = roadmap.get("phases", [])
        for phase in phases:
            phase_num = phase.get("phase_number", 1)
            phase_name = phase.get("name", "Phase")
        
            content += f"### Phase {phase_num}: {phase_name}\n\n"
        
            tasks = phase.get("tasks", [])
            relevant_tasks = []
        
            for task in tasks:
                task_name = task.get("name", "").lower()
                task_obj = task.get("objective", "").lower()
            
                # Filter tasks based on role
                if "backend" in member_role.lower():
                    if any(word in task_name or word in task_obj for word in ["api", "backend", "server", "database", "endpoint"]):
                        relevant_tasks.append(task)
                elif "frontend" in member_role.lower():
                    if any(word in task_name or word in task_obj for word in ["frontend", "ui", "component", "page", "design"]):
                        relevant_tasks.append(task)
                else:
                    relevant_tasks.append(task)
        
            if relevant_tasks:
                for task in relevant_tasks:
                    task_num = task.get("task_number", 1)
                    task_name = task.get("name", "Task")
                    objective = task.get("objective", "")
                    files = task.get("files", [])
                    acceptance = task.get("acceptance_criteria", "")
                
                    content += f"#### Task {phase_num}.{task_num}: {task_name}\n\n"
                    content += f"**Your Objective**: {objective}\n\n"
                
                    if files:
                        content += "**Files You'll Work On**:\n"
                        for file in files:
                            content += f"- [ ] `{file}`\n"
                        content += "\n"
                
                    content += f"**Done When**: {acceptance}\n\n"
                    content += "---\n\n"
            else:
                content += f"_No specific tasks for your role in this phase. Support other team members._\n\n"
        
        content += """
    ---

    ## Collaboration

    ### Your Teammates
    Check the `team/` folder for other team members' tasks.

    ### Communication
    - Update your task checkboxes as you progress
    - Note any blockers in your tasks
    - Coordinate with team on dependencies

    ### Code Review
    - Review PRs related to your area
    - Provide constructive feedback
    - Learn from others' implementations

    ---

    ## Your Development Workflow

    1. **Pick a Task** from your list above
    2. **Read Specs** from relevant documentation
    3. **Implement** following architecture patterns
    4. **Test** your implementation
    5. **Check Off** the task when complete
    6. **Move to Next** task

    ---

    **Remember**: You're part of a team. Quality code and clear communication are key to success.
    """
        
        try:
            member_name_file = member_name.lower().replace(" ", "-")
            member_role_file = member_role.lower().replace(" ", "-")
            file_path = os.path.join(self.project_dir, "team", f"{member_name_file}-{member_role_file}.md")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error generating team member file: {e}")
            return False

    def _write_file(self, relative_path: str, content: str) -> bool:
        """Write a file to the project directory."""
        try:
            full_path = os.path.join(self.project_dir, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing {relative_path}: {e}")
            return False
