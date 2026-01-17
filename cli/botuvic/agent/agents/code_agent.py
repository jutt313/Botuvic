"""
CodeAgent - Silent File Generator for BOTUVIC.
Receives handoff from MainAgent and generates project structure.
Implements 9 steps: folder, database, config, skeleton, docs, deps, roadmap, verify.
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from ..tools import AgentTools

console = Console()


class CodeAgent:
    """
    Silent worker that generates project files.
    Does NOT talk to users - reports to MainAgent only.
    """

    # System prompt embedded directly
    SYSTEM_PROMPT = """# CodeAgent - Complete System Prompt

## IDENTITY

You are **CodeAgent** - a silent worker under MainAgent. You generate project structure, database, skeleton files, and documentation.

**You do NOT talk to users.** MainAgent handles all communication.
**You only receive instructions from MainAgent and execute them.**

---

## YOUR ROLE

```
MainAgent (talks to user, plans everything)
    ↓ sends complete plan
CodeAgent (YOU - creates files silently)
    ↓ files ready
LiveAgent (monitors code)
```

---

## EXECUTION ORDER (MUST FOLLOW)

### Step 1: Create Project Root
### Step 2: Database Setup (FIRST - Everything depends on this)
### Step 3: Create Folder Structure
### Step 4: Create Configuration Files
### Step 5: Create Skeleton Files
### Step 6: Create Documentation
### Step 7: Install Dependencies
### Step 8: Create Roadmap for User
### Step 9: Final Verification

---

## PERMISSION RULES

1. **Ask before EVERY file creation**
2. **Ask before EVERY terminal command**
3. **Show progress (file X of Y)**
4. **Allow skip individual files**
5. **Allow stop all**
6. **Allow view full file before accepting**

---

## ERROR HANDLING

**If file creation fails:** Report error with suggestion
**If npm install fails:** Report error with suggestion

---

## OUTPUT TO MAINAGENT

Always report back to MainAgent with status, progress, and any errors."""

    def __init__(
        self,
        llm_client,
        storage,
        project_dir: str,
        tools: AgentTools = None
    ):
        """
        Initialize CodeAgent.

        Args:
            llm_client: LLM client for AI interactions
            storage: Storage system
            project_dir: Project root directory
            tools: AgentTools instance (optional, will create if not provided)
        """
        self.llm = llm_client
        self.storage = storage
        self.project_dir = project_dir
        self.tools = tools or AgentTools(project_dir=project_dir, storage=storage)

        # Progress tracking
        self.files_created = 0
        self.folders_created = 0
        self.errors = []
        self.todos = []

        # System prompt is embedded in class (no file loading needed)

    # =========================================================================
    # MAIN EXECUTION
    # =========================================================================

    def execute(self, handoff_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute project generation from handoff package.

        Args:
            handoff_package: Complete package from MainAgent

        Returns:
            Dict with results
        """
        console.print("\n[bold cyan]CodeAgent: Starting project generation...[/bold cyan]\n")

        # Extract data from handoff
        project = handoff_package.get("project", {})
        tech_stack = handoff_package.get("tech_stack", {})
        design = handoff_package.get("design", {})
        self.todos = handoff_package.get("todos", [])

        project_name = project.get("project_name", "my-project")
        project_type = project.get("project_type", "web_app")

        # Reset counters
        self.files_created = 0
        self.folders_created = 0
        self.errors = []

        try:
            # Step 1: Create project root
            self._update_todo(1, "in_progress")
            self._step_1_create_root(project_name)
            self._update_todo(1, "complete")

            # Step 2: Database setup (only if backend needed)
            backend_needed = tech_stack.get("backend_needed", True)
            if backend_needed:
                self._update_todo(2, "in_progress")
                self._step_2_database_setup(design, tech_stack)
                self._update_todo(2, "complete")
            else:
                self._update_todo(2, "skipped")
                console.print("[dim]Step 2: Skipping database (no backend needed)[/dim]")

            # Step 3: Create folder structure
            self._update_todo(3, "in_progress")
            self._step_3_folder_structure(project_type, tech_stack)
            self._update_todo(3, "complete")

            # Step 4: Create configuration files
            self._update_todo(4, "in_progress")
            self._step_4_config_files(project_name, tech_stack)
            self._update_todo(4, "complete")

            # Step 5: Create skeleton files
            self._update_todo(5, "in_progress")
            self._step_5_skeleton_files(project, tech_stack, design)
            self._update_todo(5, "complete")

            # Step 6: Generate documentation
            self._update_todo(6, "in_progress")
            self._step_6_documentation(project, tech_stack, design)
            self._update_todo(6, "complete")

            # Step 7: Install dependencies
            self._update_todo(7, "in_progress")
            self._step_7_install_dependencies(tech_stack)
            self._update_todo(7, "complete")

            # Step 8: Final verification
            verification = self._step_8_verification(tech_stack)

            # Generate result
            return {
                "success": True,
                "files_created": self.files_created,
                "folders_created": self.folders_created,
                "errors": self.errors,
                "verification": verification,
                "next_steps": self._get_next_steps(tech_stack)
            }

        except Exception as e:
            console.print(f"[red]CodeAgent Error: {e}[/red]")
            self.errors.append(str(e))
            return {
                "success": False,
                "error": str(e),
                "files_created": self.files_created,
                "folders_created": self.folders_created
            }

    def _update_todo(self, todo_id: int, status: str):
        """Update todo status."""
        for todo in self.todos:
            if todo.get("id") == todo_id:
                todo["status"] = status
                break

    # =========================================================================
    # STEP 1: CREATE PROJECT ROOT
    # =========================================================================

    def _step_1_create_root(self, project_name: str):
        """Create project root folder."""
        console.print("[dim]Step 1: Creating project root...[/dim]")

        # The project_dir should already exist from CLI selection
        # Just ensure it exists
        if not os.path.exists(self.project_dir):
            result = self.tools.create_folder("")
            if result.get("success"):
                self.folders_created += 1

        console.print(f"[green]✓[/green] Project root: {self.project_dir}")

    # =========================================================================
    # STEP 2: DATABASE SETUP
    # =========================================================================

    def _step_2_database_setup(self, design: Dict, tech_stack: Dict):
        """Generate database schema and setup files."""
        console.print("[dim]Step 2: Setting up database...[/dim]")

        # Create database folder
        self.tools.create_folder("database")
        self.folders_created += 1

        # Get database info
        db_config = tech_stack.get("database", {})
        db_type = db_config.get("type", "PostgreSQL")
        db_provider = db_config.get("provider", "Supabase")

        # Generate schema.sql
        schema_sql = self._generate_schema_sql(design, db_type)
        result = self.tools.write_file("database/schema.sql", schema_sql)
        if result.get("success"):
            self.files_created += 1

        # Generate seed.sql
        seed_sql = self._generate_seed_sql(design)
        result = self.tools.write_file("database/seed.sql", seed_sql)
        if result.get("success"):
            self.files_created += 1

        # Create migrations folder
        self.tools.create_folder("database/migrations")
        self.folders_created += 1

        console.print(f"[green]✓[/green] Database schema created")

    def _generate_schema_sql(self, design: Dict, db_type: str) -> str:
        """Generate complete SQL schema."""
        db_design = design.get("database", {})
        tables = db_design.get("tables", [])

        # If no tables in design, generate basic schema
        if not tables:
            tables = self._generate_default_tables()

        schema = f"""-- =============================================
-- DATABASE SCHEMA
-- Generated by BOTUVIC CodeAgent
-- Database: {db_type}
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- =============================================

-- Enable UUID extension (PostgreSQL)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

"""
        for table in tables:
            schema += self._generate_table_sql(table)
            schema += "\n"

        # Add update trigger function
        schema += """
-- =============================================
-- FUNCTIONS & TRIGGERS
-- =============================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

"""
        return schema

    def _generate_table_sql(self, table: Dict) -> str:
        """Generate SQL for a single table."""
        name = table.get("name", "table")
        columns = table.get("columns", [])

        if not columns:
            columns = [
                {"name": "id", "type": "UUID", "constraints": ["PRIMARY KEY", "DEFAULT uuid_generate_v4()"]},
                {"name": "created_at", "type": "TIMESTAMPTZ", "constraints": ["DEFAULT NOW()"]},
                {"name": "updated_at", "type": "TIMESTAMPTZ", "constraints": ["DEFAULT NOW()"]}
            ]

        sql = f"-- Table: {name}\n"
        sql += f"CREATE TABLE {name} (\n"

        col_lines = []
        for col in columns:
            col_name = col.get("name")
            col_type = col.get("type", "TEXT")
            constraints = col.get("constraints", [])
            constraint_str = " ".join(constraints)
            col_lines.append(f"    {col_name} {col_type} {constraint_str}".strip())

        sql += ",\n".join(col_lines)
        sql += "\n);\n"

        # Add indexes
        indexes = table.get("indexes", [])
        for idx in indexes:
            sql += f"CREATE INDEX idx_{name}_{idx} ON {name}({idx});\n"

        return sql

    def _generate_default_tables(self) -> List[Dict]:
        """Generate default table structure."""
        return [
            {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "UUID", "constraints": ["PRIMARY KEY", "DEFAULT uuid_generate_v4()"]},
                    {"name": "email", "type": "TEXT", "constraints": ["UNIQUE", "NOT NULL"]},
                    {"name": "username", "type": "TEXT", "constraints": ["UNIQUE", "NOT NULL"]},
                    {"name": "password_hash", "type": "TEXT", "constraints": ["NOT NULL"]},
                    {"name": "full_name", "type": "TEXT"},
                    {"name": "avatar_url", "type": "TEXT"},
                    {"name": "created_at", "type": "TIMESTAMPTZ", "constraints": ["DEFAULT NOW()"]},
                    {"name": "updated_at", "type": "TIMESTAMPTZ", "constraints": ["DEFAULT NOW()"]}
                ],
                "indexes": ["email", "username"]
            }
        ]

    def _generate_seed_sql(self, design: Dict) -> str:
        """Generate seed data SQL."""
        return """-- =============================================
-- SEED DATA
-- Generated by BOTUVIC CodeAgent
-- =============================================

-- Example seed data (commented out)
-- INSERT INTO users (email, username, password_hash, full_name)
-- VALUES ('demo@example.com', 'demo', 'hashed_password', 'Demo User');
"""

    # =========================================================================
    # STEP 3: FOLDER STRUCTURE
    # =========================================================================

    def _step_3_folder_structure(self, project_type: str, tech_stack: Dict):
        """Create complete folder structure."""
        console.print("[dim]Step 3: Creating folder structure...[/dim]")

        frontend = tech_stack.get("frontend", {}).get("framework", "Next.js")

        # Determine structure based on project type
        if project_type == "web_app":
            folders = self._get_web_app_folders(frontend)
        elif project_type == "mobile_app":
            folders = self._get_mobile_app_folders()
        elif project_type == "cli":
            folders = self._get_cli_folders()
        elif project_type == "api":
            folders = self._get_api_folders()
        else:
            folders = self._get_web_app_folders(frontend)

        # Create all folders
        for folder in folders:
            result = self.tools.create_folder(folder)
            if result.get("success") and not result.get("exists"):
                self.folders_created += 1

        console.print(f"[green]✓[/green] Created {len(folders)} folders")

    def _get_web_app_folders(self, frontend: str) -> List[str]:
        """Get folder structure for web app."""
        if "next" in frontend.lower():
            return [
                "frontend/src/app",
                "frontend/src/app/(auth)/login",
                "frontend/src/app/(auth)/signup",
                "frontend/src/app/(dashboard)/dashboard",
                "frontend/src/app/(dashboard)/settings",
                "frontend/src/app/api",
                "frontend/src/components/ui",
                "frontend/src/components/forms",
                "frontend/src/components/layout",
                "frontend/src/components/features",
                "frontend/src/lib",
                "frontend/src/hooks",
                "frontend/src/stores",
                "frontend/src/types",
                "frontend/src/styles",
                "frontend/public/images",
                "docs"
            ]
        else:
            return [
                "frontend/src/components",
                "frontend/src/pages",
                "frontend/src/lib",
                "frontend/src/hooks",
                "frontend/src/stores",
                "frontend/public",
                "docs"
            ]

    def _get_mobile_app_folders(self) -> List[str]:
        """Get folder structure for mobile app."""
        return [
            "app/(tabs)",
            "app/(auth)",
            "components",
            "lib",
            "hooks",
            "stores",
            "types",
            "assets/images",
            "docs"
        ]

    def _get_cli_folders(self) -> List[str]:
        """Get folder structure for CLI."""
        return [
            "src/commands",
            "src/utils",
            "src/config",
            "bin",
            "docs"
        ]

    def _get_api_folders(self) -> List[str]:
        """Get folder structure for API."""
        return [
            "app/routers",
            "app/models",
            "app/schemas",
            "app/services",
            "app/core",
            "tests",
            "docs"
        ]

    # =========================================================================
    # STEP 4: CONFIGURATION FILES
    # =========================================================================

    def _step_4_config_files(self, project_name: str, tech_stack: Dict):
        """Create configuration files."""
        console.print("[dim]Step 4: Creating configuration files...[/dim]")

        frontend = tech_stack.get("frontend", {})
        framework = frontend.get("framework", "Next.js")

        # package.json
        if "next" in framework.lower() or "react" in framework.lower():
            package_json = self._generate_package_json(project_name, tech_stack)
            result = self.tools.write_file("frontend/package.json", package_json)
            if result.get("success"):
                self.files_created += 1

            # tsconfig.json
            tsconfig = self._generate_tsconfig()
            result = self.tools.write_file("frontend/tsconfig.json", tsconfig)
            if result.get("success"):
                self.files_created += 1

            # tailwind.config.js
            if "tailwind" in frontend.get("styling", "").lower():
                tailwind = self._generate_tailwind_config()
                result = self.tools.write_file("frontend/tailwind.config.js", tailwind)
                if result.get("success"):
                    self.files_created += 1

            # next.config.js
            if "next" in framework.lower():
                next_config = self._generate_next_config()
                result = self.tools.write_file("frontend/next.config.js", next_config)
                if result.get("success"):
                    self.files_created += 1

        # .gitignore
        gitignore = self._generate_gitignore()
        result = self.tools.write_file(".gitignore", gitignore)
        if result.get("success"):
            self.files_created += 1

        # .env.example
        env_example = self._generate_env_example(tech_stack)
        result = self.tools.write_file(".env.example", env_example)
        if result.get("success"):
            self.files_created += 1

        console.print(f"[green]✓[/green] Configuration files created")

    def _generate_package_json(self, name: str, tech_stack: Dict) -> str:
        """Generate package.json."""
        frontend = tech_stack.get("frontend", {})
        db_provider = tech_stack.get("database", {}).get("provider", "").lower()

        deps = {
            "next": "^14.0.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "zustand": "^4.4.0",
            "zod": "^3.22.0"
        }

        # Add styling deps
        if "tailwind" in frontend.get("styling", "").lower():
            deps["tailwindcss"] = "^3.3.0"
            deps["autoprefixer"] = "^10.4.0"
            deps["postcss"] = "^8.4.0"

        # Add database deps
        if "supabase" in db_provider:
            deps["@supabase/supabase-js"] = "^2.38.0"
            deps["@supabase/ssr"] = "^0.1.0"

        dev_deps = {
            "@types/node": "^20.0.0",
            "@types/react": "^18.2.0",
            "typescript": "^5.0.0"
        }

        package = {
            "name": name.lower().replace(" ", "-"),
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint"
            },
            "dependencies": deps,
            "devDependencies": dev_deps
        }

        return json.dumps(package, indent=2)

    def _generate_tsconfig(self) -> str:
        """Generate tsconfig.json."""
        config = {
            "compilerOptions": {
                "target": "ES2017",
                "lib": ["dom", "dom.iterable", "esnext"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [{"name": "next"}],
                "paths": {
                    "@/*": ["./src/*"]
                }
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"]
        }
        return json.dumps(config, indent=2)

    def _generate_tailwind_config(self) -> str:
        """Generate tailwind.config.js."""
        return """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
      },
    },
  },
  plugins: [],
}
"""

    def _generate_next_config(self) -> str:
        """Generate next.config.js."""
        return """/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: [],
  },
}

module.exports = nextConfig
"""

    def _generate_gitignore(self) -> str:
        """Generate .gitignore."""
        return """# Dependencies
node_modules/
.pnp
.pnp.js

# Build
.next/
out/
build/
dist/

# Environment
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
coverage/

# Misc
*.pem
.botuvic/backups/
"""

    def _generate_env_example(self, tech_stack: Dict) -> str:
        """Generate .env.example."""
        db = tech_stack.get("database", {})
        provider = db.get("provider", "").lower()

        env = """# Environment Variables
# Copy this file to .env.local and fill in your values

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000

"""
        if "supabase" in provider:
            env += """# Supabase
# Get these from: https://supabase.com/dashboard/project/_/settings/api
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
"""
        else:
            env += """# Database
DATABASE_URL=postgresql://user:password@localhost:5432/database
"""

        return env

    # =========================================================================
    # STEP 5: SKELETON FILES
    # =========================================================================

    def _step_5_skeleton_files(self, project: Dict, tech_stack: Dict, design: Dict):
        """Create skeleton files with structure, imports, types."""
        console.print("[dim]Step 5: Creating skeleton files...[/dim]")

        # Get frontend and backend info
        frontends = tech_stack.get("frontends", {})
        backend = tech_stack.get("backend", {})
        
        # Legacy support for old format
        if not frontends:
            frontend = tech_stack.get("frontend", {})
            framework = frontend.get("framework", "")
            frontends = {"web": framework}

        # Generate frontend skeletons
        web_framework = frontends.get("web", "")
        mobile_framework = frontends.get("mobile", "")
        desktop_framework = frontends.get("desktop", "")
        cli_framework = frontends.get("cli", "")

        # Web Frontend
        if web_framework:
            if "next" in web_framework.lower():
                self._create_nextjs_skeletons(project, tech_stack, design)
            elif "react" in web_framework.lower():
                self._create_react_skeletons(project, tech_stack, design)
            elif "vue" in web_framework.lower():
                self._create_vue_skeletons(project, tech_stack, design)
            elif "svelte" in web_framework.lower():
                self._create_svelte_skeletons(project, tech_stack, design)

        # Mobile Frontend
        if mobile_framework:
            if "flutter" in mobile_framework.lower():
                self._create_flutter_skeletons(project, tech_stack, design)
            elif "react native" in mobile_framework.lower() or "expo" in mobile_framework.lower():
                self._create_react_native_skeletons(project, tech_stack, design)

        # CLI
        if cli_framework:
            self._create_cli_skeletons(project, tech_stack, design, cli_framework)

        # Backend (only generate if backend is needed and specified)
        backend_needed = tech_stack.get("backend_needed", True)
        if backend_needed and backend:
            backend_framework = backend.get("framework", "") if isinstance(backend, dict) else str(backend)
            backend_language = backend.get("language", "") if isinstance(backend, dict) else ""
            
            if "fastapi" in backend_framework.lower() or "python" in backend_language.lower():
                self._create_python_fastapi_skeletons(project, tech_stack, design)
            elif "express" in backend_framework.lower() or "node" in backend_language.lower():
                self._create_nodejs_skeletons(project, tech_stack, design)
            elif "go" in backend_language.lower() or "gin" in backend_framework.lower():
                self._create_go_skeletons(project, tech_stack, design)
        elif not backend_needed:
            console.print("[dim]  → Skipping backend (not needed for this project)[/dim]")

        console.print(f"[green]✓[/green] Skeleton files created")

    def _create_nextjs_skeletons(self, project: Dict, tech_stack: Dict, design: Dict):
        """Create Next.js skeleton files."""
        # Root layout
        layout = self._generate_root_layout(project)
        result = self.tools.write_file("frontend/src/app/layout.tsx", layout)
        if result.get("success"):
            self.files_created += 1

        # Home page
        home = self._generate_home_page(project)
        result = self.tools.write_file("frontend/src/app/page.tsx", home)
        if result.get("success"):
            self.files_created += 1

        # Global CSS
        css = self._generate_global_css()
        result = self.tools.write_file("frontend/src/app/globals.css", css)
        if result.get("success"):
            self.files_created += 1

        # Utils
        utils = self._generate_utils()
        result = self.tools.write_file("frontend/src/lib/utils.ts", utils)
        if result.get("success"):
            self.files_created += 1

        # Supabase client (if using)
        if "supabase" in tech_stack.get("database", {}).get("provider", "").lower():
            supabase = self._generate_supabase_client()
            result = self.tools.write_file("frontend/src/lib/supabase/client.ts", supabase)
            if result.get("success"):
                self.files_created += 1

        # Button component
        button = self._generate_button_component()
        result = self.tools.write_file("frontend/src/components/ui/Button.tsx", button)
        if result.get("success"):
            self.files_created += 1

        # Login page
        login = self._generate_login_page()
        result = self.tools.write_file("frontend/src/app/(auth)/login/page.tsx", login)
        if result.get("success"):
            self.files_created += 1

        # Dashboard page
        dashboard = self._generate_dashboard_page()
        result = self.tools.write_file("frontend/src/app/(dashboard)/dashboard/page.tsx", dashboard)
        if result.get("success"):
            self.files_created += 1

    def _generate_root_layout(self, project: Dict) -> str:
        """Generate root layout.tsx."""
        name = project.get("project_name", "My App")
        return f'''import type {{ Metadata }} from 'next'
import {{ Inter }} from 'next/font/google'
import './globals.css'

const inter = Inter({{ subsets: ['latin'] }})

export const metadata: Metadata = {{
  title: '{name}',
  description: 'Built with BOTUVIC',
}}

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode
}}) {{
  return (
    <html lang="en">
      <body className={{inter.className}}>
        {{children}}
      </body>
    </html>
  )
}}
'''

    def _generate_home_page(self, project: Dict) -> str:
        """Generate home page.tsx."""
        name = project.get("project_name", "My App")
        return f'''export default function Home() {{
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-4">{name}</h1>
      <p className="text-gray-600 mb-8">Welcome to your new project!</p>
      <div className="flex gap-4">
        <a
          href="/login"
          className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Get Started
        </a>
        <a
          href="/dashboard"
          className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Dashboard
        </a>
      </div>
    </main>
  )
}}
'''

    def _generate_global_css(self) -> str:
        """Generate globals.css."""
        return """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-rgb: 255, 255, 255;
}

body {
  color: rgb(var(--foreground-rgb));
  background: rgb(var(--background-rgb));
}
"""

    def _generate_utils(self) -> str:
        """Generate utils.ts."""
        return '''import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
'''

    def _generate_supabase_client(self) -> str:
        """Generate Supabase client."""
        return '''import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
'''

    def _generate_button_component(self) -> str:
        """Generate Button component."""
        return '''import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 disabled:opacity-50'

    const variants = {
      primary: 'bg-primary-600 text-white hover:bg-primary-700',
      secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200',
      outline: 'border border-gray-300 hover:bg-gray-50',
    }

    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2',
      lg: 'px-6 py-3 text-lg',
    }

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={isLoading}
        {...props}
      >
        {isLoading ? <span className="mr-2 animate-spin">...</span> : null}
        {children}
      </button>
    )
  }
)
Button.displayName = 'Button'

export { Button }
'''

    def _generate_login_page(self) -> str:
        """Generate login page."""
        return '''\'use client\'

import { useState } from 'react'
import { Button } from '@/components/ui/Button'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    // TODO: Implement login logic
    console.log('Login:', { email, password })

    setIsLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-8">Sign In</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
              required
            />
          </div>

          <Button type="submit" className="w-full" isLoading={isLoading}>
            Sign In
          </Button>
        </form>

        <p className="text-center mt-4 text-sm text-gray-600">
          Don\'t have an account? <a href="/signup" className="text-primary-600">Sign up</a>
        </p>
      </div>
    </div>
  )
}
'''

    def _generate_dashboard_page(self) -> str:
        """Generate dashboard page."""
        return '''export default function DashboardPage() {
  return (
    <div className="min-h-screen p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-gray-600">Welcome back!</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Stats Cards */}
        <div className="p-6 bg-white rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Users</h3>
          <p className="text-3xl font-bold mt-2">0</p>
        </div>

        <div className="p-6 bg-white rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Active Sessions</h3>
          <p className="text-3xl font-bold mt-2">0</p>
        </div>

        <div className="p-6 bg-white rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Revenue</h3>
          <p className="text-3xl font-bold mt-2">$0</p>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mt-8 p-6 bg-white rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        <p className="text-gray-500">No recent activity</p>
      </div>
    </div>
  )
}
'''

    # =========================================================================
    # PYTHON/FASTAPI SKELETONS
    # =========================================================================

    def _create_python_fastapi_skeletons(self, project: Dict, tech_stack: Dict, design: Dict):
        """Create Python/FastAPI skeleton files."""
        console.print("[dim]  → Creating Python/FastAPI backend...[/dim]")
        
        name = project.get("project_name", "my_app").lower().replace(" ", "_").replace("-", "_")
        
        # Create backend folder structure
        self.tools.create_folder("backend/app/routers")
        self.tools.create_folder("backend/app/models")
        self.tools.create_folder("backend/app/schemas")
        self.tools.create_folder("backend/app/services")
        self.tools.create_folder("backend/app/core")
        self.tools.create_folder("backend/tests")
        self.folders_created += 6

        # main.py
        main_py = self._generate_fastapi_main(name)
        result = self.tools.write_file("backend/app/main.py", main_py)
        if result.get("success"):
            self.files_created += 1

        # config.py
        config_py = self._generate_fastapi_config()
        result = self.tools.write_file("backend/app/core/config.py", config_py)
        if result.get("success"):
            self.files_created += 1

        # database.py
        database_py = self._generate_fastapi_database(tech_stack)
        result = self.tools.write_file("backend/app/core/database.py", database_py)
        if result.get("success"):
            self.files_created += 1

        # User model
        user_model = self._generate_fastapi_user_model()
        result = self.tools.write_file("backend/app/models/user.py", user_model)
        if result.get("success"):
            self.files_created += 1

        # User schema
        user_schema = self._generate_fastapi_user_schema()
        result = self.tools.write_file("backend/app/schemas/user.py", user_schema)
        if result.get("success"):
            self.files_created += 1

        # Auth router
        auth_router = self._generate_fastapi_auth_router()
        result = self.tools.write_file("backend/app/routers/auth.py", auth_router)
        if result.get("success"):
            self.files_created += 1

        # requirements.txt
        requirements = self._generate_python_requirements(tech_stack)
        result = self.tools.write_file("backend/requirements.txt", requirements)
        if result.get("success"):
            self.files_created += 1

    def _generate_fastapi_main(self, name: str) -> str:
        """Generate FastAPI main.py."""
        return f'''"""
{name} - FastAPI Backend
Generated by BOTUVIC CodeAgent
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth

app = FastAPI(
    title="{name}",
    description="API built with BOTUVIC",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


@app.get("/")
async def root():
    return {{"message": "Welcome to {name} API"}}


@app.get("/health")
async def health_check():
    return {{"status": "healthy"}}
'''

    def _generate_fastapi_config(self) -> str:
        """Generate FastAPI config.py."""
        return '''from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # App
    APP_NAME: str = "My App"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/db"
    
    # Auth
    SECRET_KEY: str = "change-this-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"


settings = Settings()
'''

    def _generate_fastapi_database(self, tech_stack: Dict) -> str:
        """Generate FastAPI database.py."""
        db = tech_stack.get("database", {})
        provider = db.get("provider", "").lower()
        
        if "supabase" in provider:
            return '''from supabase import create_client, Client
from app.core.config import settings

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)


def get_supabase() -> Client:
    return supabase
'''
        else:
            return '''from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

    def _generate_fastapi_user_model(self) -> str:
        """Generate FastAPI user model."""
        return '''from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
'''

    def _generate_fastapi_user_schema(self) -> str:
        """Generate FastAPI user schema."""
        return '''from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
'''

    def _generate_fastapi_auth_router(self) -> str:
        """Generate FastAPI auth router."""
        return '''from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.schemas.user import UserCreate, UserLogin, UserResponse, Token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate):
    """Create new user account."""
    # TODO: Implement signup logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Signup not implemented yet"
    )


@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    """Authenticate user and return token."""
    # TODO: Implement login logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login not implemented yet"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user."""
    # TODO: Implement get current user logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get current user not implemented yet"
    )
'''

    def _generate_python_requirements(self, tech_stack: Dict) -> str:
        """Generate Python requirements.txt."""
        db = tech_stack.get("database", {})
        provider = db.get("provider", "").lower()
        
        reqs = """# Core
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

"""
        if "supabase" in provider:
            reqs += """# Database (Supabase)
supabase>=2.0.0
"""
        else:
            reqs += """# Database
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9
alembic>=1.12.0
"""
        
        reqs += """
# Utils
python-dotenv>=1.0.0
httpx>=0.25.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
"""
        return reqs

    # =========================================================================
    # REACT SKELETONS (Vite)
    # =========================================================================

    def _create_react_skeletons(self, project: Dict, tech_stack: Dict, design: Dict):
        """Create React (Vite) skeleton files."""
        console.print("[dim]  → Creating React frontend...[/dim]")
        
        # Create folders
        self.tools.create_folder("frontend/src/components")
        self.tools.create_folder("frontend/src/pages")
        self.tools.create_folder("frontend/src/hooks")
        self.tools.create_folder("frontend/src/lib")
        self.tools.create_folder("frontend/src/stores")
        self.folders_created += 5

        # vite.config.ts
        vite_config = self._generate_vite_config()
        result = self.tools.write_file("frontend/vite.config.ts", vite_config)
        if result.get("success"):
            self.files_created += 1

        # main.tsx
        main_tsx = self._generate_react_main()
        result = self.tools.write_file("frontend/src/main.tsx", main_tsx)
        if result.get("success"):
            self.files_created += 1

        # App.tsx
        app_tsx = self._generate_react_app(project)
        result = self.tools.write_file("frontend/src/App.tsx", app_tsx)
        if result.get("success"):
            self.files_created += 1

    def _generate_vite_config(self) -> str:
        """Generate vite.config.ts."""
        return '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
'''

    def _generate_react_main(self) -> str:
        """Generate React main.tsx."""
        return '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
'''

    def _generate_react_app(self, project: Dict) -> str:
        """Generate React App.tsx."""
        name = project.get("project_name", "My App")
        return f'''function App() {{
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-4">{name}</h1>
      <p className="text-gray-600 mb-8">Welcome to your React app!</p>
    </div>
  )
}}

export default App
'''

    # =========================================================================
    # VUE SKELETONS
    # =========================================================================

    def _create_vue_skeletons(self, project: Dict, tech_stack: Dict, design: Dict):
        """Create Vue skeleton files."""
        console.print("[dim]  → Creating Vue frontend...[/dim]")
        
        # Create folders
        self.tools.create_folder("frontend/src/components")
        self.tools.create_folder("frontend/src/views")
        self.tools.create_folder("frontend/src/stores")
        self.folders_created += 3

        # App.vue
        app_vue = self._generate_vue_app(project)
        result = self.tools.write_file("frontend/src/App.vue", app_vue)
        if result.get("success"):
            self.files_created += 1

        # main.ts
        main_ts = self._generate_vue_main()
        result = self.tools.write_file("frontend/src/main.ts", main_ts)
        if result.get("success"):
            self.files_created += 1

    def _generate_vue_app(self, project: Dict) -> str:
        """Generate Vue App.vue."""
        name = project.get("project_name", "My App")
        return f'''<script setup lang="ts">
// {name} - Vue App
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center p-8">
    <h1 class="text-4xl font-bold mb-4">{name}</h1>
    <p class="text-gray-600 mb-8">Welcome to your Vue app!</p>
  </div>
</template>

<style scoped>
</style>
'''

    def _generate_vue_main(self) -> str:
        """Generate Vue main.ts."""
        return '''import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

createApp(App).mount('#app')
'''

    # =========================================================================
    # SVELTE SKELETONS
    # =========================================================================

    def _create_svelte_skeletons(self, project: Dict, tech_stack: Dict, design: Dict):
        """Create Svelte skeleton files."""
        console.print("[dim]  → Creating Svelte frontend...[/dim]")
        
        # Create folders
        self.tools.create_folder("frontend/src/lib")
        self.tools.create_folder("frontend/src/routes")
        self.folders_created += 2

        # +page.svelte
        page = self._generate_svelte_page(project)
        result = self.tools.write_file("frontend/src/routes/+page.svelte", page)
        if result.get("success"):
            self.files_created += 1

    def _generate_svelte_page(self, project: Dict) -> str:
        """Generate Svelte +page.svelte."""
        name = project.get("project_name", "My App")
        return f'''<script lang="ts">
  // {name}
</script>

<div class="min-h-screen flex flex-col items-center justify-center p-8">
  <h1 class="text-4xl font-bold mb-4">{name}</h1>
  <p class="text-gray-600 mb-8">Welcome to your Svelte app!</p>
</div>

<style>
</style>
'''

    # =========================================================================
    # FLUTTER SKELETONS
    # =========================================================================

    def _create_flutter_skeletons(self, project: Dict, tech_stack: Dict, design: Dict):
        """Create Flutter skeleton files."""
        console.print("[dim]  → Creating Flutter mobile app...[/dim]")
        
        name = project.get("project_name", "my_app").lower().replace(" ", "_").replace("-", "_")
        
        # Create folders
        self.tools.create_folder("mobile/lib/screens")
        self.tools.create_folder("mobile/lib/widgets")
        self.tools.create_folder("mobile/lib/services")
        self.tools.create_folder("mobile/lib/models")
        self.folders_created += 4

        # main.dart
        main_dart = self._generate_flutter_main(project)
        result = self.tools.write_file("mobile/lib/main.dart", main_dart)
        if result.get("success"):
            self.files_created += 1

        # home_screen.dart
        home = self._generate_flutter_home(project)
        result = self.tools.write_file("mobile/lib/screens/home_screen.dart", home)
        if result.get("success"):
            self.files_created += 1

        # pubspec.yaml
        pubspec = self._generate_pubspec(project, tech_stack)
        result = self.tools.write_file("mobile/pubspec.yaml", pubspec)
        if result.get("success"):
            self.files_created += 1

    def _generate_flutter_main(self, project: Dict) -> str:
        """Generate Flutter main.dart."""
        name = project.get("project_name", "My App")
        return f'''import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {{
  runApp(const MyApp());
}}

class MyApp extends StatelessWidget {{
  const MyApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{name}',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }}
}}
'''

    def _generate_flutter_home(self, project: Dict) -> str:
        """Generate Flutter home_screen.dart."""
        name = project.get("project_name", "My App")
        return f'''import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {{
  const HomeScreen({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{name}'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'Welcome to {name}!',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {{
                // TODO: Add navigation
              }},
              child: const Text('Get Started'),
            ),
          ],
        ),
      ),
    );
  }}
}}
'''

    def _generate_pubspec(self, project: Dict, tech_stack: Dict) -> str:
        """Generate Flutter pubspec.yaml."""
        name = project.get("project_name", "my_app").lower().replace(" ", "_").replace("-", "_")
        return f'''name: {name}
description: "Built with BOTUVIC"
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.6
  http: ^1.1.0
  provider: ^6.1.1
  shared_preferences: ^2.2.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.1

flutter:
  uses-material-design: true
'''

    # =========================================================================
    # REACT NATIVE SKELETONS
    # =========================================================================

    def _create_react_native_skeletons(self, project: Dict, tech_stack: Dict, design: Dict):
        """Create React Native/Expo skeleton files."""
        console.print("[dim]  → Creating React Native mobile app...[/dim]")
        
        # Create folders
        self.tools.create_folder("mobile/app")
        self.tools.create_folder("mobile/components")
        self.tools.create_folder("mobile/hooks")
        self.tools.create_folder("mobile/lib")
        self.folders_created += 4

        # App.tsx
        app_tsx = self._generate_rn_app(project)
        result = self.tools.write_file("mobile/App.tsx", app_tsx)
        if result.get("success"):
            self.files_created += 1

    def _generate_rn_app(self, project: Dict) -> str:
        """Generate React Native App.tsx."""
        name = project.get("project_name", "My App")
        return f'''import {{ StatusBar }} from 'expo-status-bar';
import {{ StyleSheet, Text, View }} from 'react-native';

export default function App() {{
  return (
    <View style={{styles.container}}>
      <Text style={{styles.title}}>{name}</Text>
      <Text style={{styles.subtitle}}>Welcome to your mobile app!</Text>
      <StatusBar style="auto" />
    </View>
  );
}}

const styles = StyleSheet.create({{
  container: {{
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  }},
  title: {{
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
  }},
  subtitle: {{
    fontSize: 16,
    color: '#666',
  }},
}});
'''

    # =========================================================================
    # GO SKELETONS
    # =========================================================================

    def _create_go_skeletons(self, project: Dict, tech_stack: Dict, design: Dict):
        """Create Go skeleton files."""
        console.print("[dim]  → Creating Go backend...[/dim]")
        
        name = project.get("project_name", "myapp").lower().replace(" ", "").replace("-", "")
        
        # Create folders
        self.tools.create_folder("backend/cmd/server")
        self.tools.create_folder("backend/internal/handlers")
        self.tools.create_folder("backend/internal/models")
        self.tools.create_folder("backend/internal/database")
        self.folders_created += 4

        # main.go
        main_go = self._generate_go_main(name)
        result = self.tools.write_file("backend/cmd/server/main.go", main_go)
        if result.get("success"):
            self.files_created += 1

        # go.mod
        go_mod = self._generate_go_mod(name)
        result = self.tools.write_file("backend/go.mod", go_mod)
        if result.get("success"):
            self.files_created += 1

    def _generate_go_main(self, name: str) -> str:
        """Generate Go main.go."""
        return f'''package main

import (
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
)

func main() {{
	r := gin.Default()

	// CORS
	r.Use(func(c *gin.Context) {{
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if c.Request.Method == "OPTIONS" {{
			c.AbortWithStatus(204)
			return
		}}
		c.Next()
	}})

	// Routes
	r.GET("/", func(c *gin.Context) {{
		c.JSON(http.StatusOK, gin.H{{"message": "Welcome to {name} API"}})
	}})

	r.GET("/health", func(c *gin.Context) {{
		c.JSON(http.StatusOK, gin.H{{"status": "healthy"}})
	}})

	// Start server
	log.Println("Server starting on :8080")
	if err := r.Run(":8080"); err != nil {{
		log.Fatal(err)
	}}
}}
'''

    def _generate_go_mod(self, name: str) -> str:
        """Generate Go go.mod."""
        return f'''module {name}

go 1.21

require (
	github.com/gin-gonic/gin v1.9.1
)
'''

    # =========================================================================
    # CLI SKELETONS
    # =========================================================================

    def _create_cli_skeletons(self, project: Dict, tech_stack: Dict, design: Dict, framework: str):
        """Create CLI skeleton files."""
        console.print("[dim]  → Creating CLI application...[/dim]")
        
        name = project.get("project_name", "mycli").lower().replace(" ", "_").replace("-", "_")
        
        if "python" in framework.lower() or "typer" in framework.lower() or "click" in framework.lower():
            self._create_python_cli(project, name)
        elif "go" in framework.lower() or "cobra" in framework.lower():
            self._create_go_cli(project, name)
        elif "rust" in framework.lower() or "clap" in framework.lower():
            self._create_rust_cli(project, name)

    def _create_python_cli(self, project: Dict, name: str):
        """Create Python CLI with Typer."""
        # Create folders
        self.tools.create_folder(f"cli/{name}")
        self.tools.create_folder(f"cli/{name}/commands")
        self.folders_created += 2

        # main.py
        main_py = self._generate_python_cli_main(project, name)
        result = self.tools.write_file(f"cli/{name}/main.py", main_py)
        if result.get("success"):
            self.files_created += 1

        # requirements.txt
        reqs = """typer>=0.9.0
rich>=13.0.0
"""
        result = self.tools.write_file("cli/requirements.txt", reqs)
        if result.get("success"):
            self.files_created += 1

    def _generate_python_cli_main(self, project: Dict, name: str) -> str:
        """Generate Python CLI main.py."""
        display_name = project.get("project_name", "My CLI")
        return f'''"""
{display_name} - CLI Application
Generated by BOTUVIC CodeAgent
"""

import typer
from rich.console import Console

app = typer.Typer(help="{display_name} CLI")
console = Console()


@app.command()
def hello(name: str = "World"):
    """Say hello."""
    console.print(f"[green]Hello, {{name}}![/green]")


@app.command()
def version():
    """Show version."""
    console.print("[bold]{display_name}[/bold] v0.1.0")


if __name__ == "__main__":
    app()
'''

    def _create_go_cli(self, project: Dict, name: str):
        """Create Go CLI with Cobra."""
        # Create folders
        self.tools.create_folder("cli/cmd")
        self.folders_created += 1

        # main.go
        main_go = f'''package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{{
	Use:   "{name}",
	Short: "{project.get("project_name", "CLI")}",
	Long:  "Built with BOTUVIC",
}}

func main() {{
	if err := rootCmd.Execute(); err != nil {{
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}}
}}
'''
        result = self.tools.write_file("cli/main.go", main_go)
        if result.get("success"):
            self.files_created += 1

    def _create_rust_cli(self, project: Dict, name: str):
        """Create Rust CLI with Clap."""
        # Create folders
        self.tools.create_folder("cli/src")
        self.folders_created += 1

        # main.rs
        main_rs = f'''use clap::{{Parser, Subcommand}};

#[derive(Parser)]
#[command(name = "{name}")]
#[command(about = "{project.get("project_name", "CLI")} - Built with BOTUVIC")]
struct Cli {{
    #[command(subcommand)]
    command: Commands,
}}

#[derive(Subcommand)]
enum Commands {{
    /// Say hello
    Hello {{ name: Option<String> }},
    /// Show version
    Version,
}}

fn main() {{
    let cli = Cli::parse();

    match cli.command {{
        Commands::Hello {{ name }} => {{
            let name = name.unwrap_or_else(|| "World".to_string());
            println!("Hello, {{}}!", name);
        }}
        Commands::Version => {{
            println!("{name} v0.1.0");
        }}
    }}
}}
'''
        result = self.tools.write_file("cli/src/main.rs", main_rs)
        if result.get("success"):
            self.files_created += 1

    def _create_nodejs_skeletons(self, project: Dict, tech_stack: Dict, design: Dict):
        """Create Node.js/Express skeleton files."""
        console.print("[dim]  → Creating Node.js backend...[/dim]")
        
        # Create folders
        self.tools.create_folder("backend/src/routes")
        self.tools.create_folder("backend/src/controllers")
        self.tools.create_folder("backend/src/middleware")
        self.tools.create_folder("backend/src/models")
        self.folders_created += 4

        # index.js
        index_js = self._generate_express_index(project)
        result = self.tools.write_file("backend/src/index.js", index_js)
        if result.get("success"):
            self.files_created += 1

        # package.json
        package_json = self._generate_express_package(project)
        result = self.tools.write_file("backend/package.json", package_json)
        if result.get("success"):
            self.files_created += 1

    def _generate_express_index(self, project: Dict) -> str:
        """Generate Express index.js."""
        name = project.get("project_name", "My App")
        return f'''const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.get('/', (req, res) => {{
  res.json({{ message: 'Welcome to {name} API' }});
}});

app.get('/health', (req, res) => {{
  res.json({{ status: 'healthy' }});
}});

// Start server
app.listen(PORT, () => {{
  console.log(`Server running on port ${{PORT}}`);
}});
'''

    def _generate_express_package(self, project: Dict) -> str:
        """Generate Express package.json."""
        name = project.get("project_name", "backend").lower().replace(" ", "-")
        return json.dumps({
            "name": name,
            "version": "0.1.0",
            "main": "src/index.js",
            "scripts": {
                "dev": "nodemon src/index.js",
                "start": "node src/index.js"
            },
            "dependencies": {
                "express": "^4.18.2",
                "cors": "^2.8.5",
                "dotenv": "^16.3.1"
            },
            "devDependencies": {
                "nodemon": "^3.0.1"
            }
        }, indent=2)

    # =========================================================================
    # STEP 6: DOCUMENTATION
    # =========================================================================

    def _step_6_documentation(self, project: Dict, tech_stack: Dict, design: Dict):
        """Generate comprehensive documentation files."""
        console.print("[dim]Step 6: Creating documentation...[/dim]")

        # README.md
        readme = self._generate_readme(project, tech_stack)
        result = self.tools.write_file("README.md", readme)
        if result.get("success"):
            self.files_created += 1

        # docs/SETUP.md
        setup = self._generate_setup_doc(project, tech_stack)
        result = self.tools.write_file("docs/SETUP.md", setup)
        if result.get("success"):
            self.files_created += 1

        # docs/ROADMAP.md (includes phases, tasks, plan)
        roadmap = self._generate_roadmap_doc(project, design)
        result = self.tools.write_file("docs/ROADMAP.md", roadmap)
        if result.get("success"):
            self.files_created += 1

        # docs/TESTING.md
        testing = self._generate_testing_doc(project, tech_stack)
        result = self.tools.write_file("docs/TESTING.md", testing)
        if result.get("success"):
            self.files_created += 1

        # docs/API.md (if backend)
        backend = tech_stack.get("backend", {})
        if backend:
            api_doc = self._generate_api_doc(project, design)
            result = self.tools.write_file("docs/API.md", api_doc)
            if result.get("success"):
                self.files_created += 1

        # docs/AI_INSTRUCTIONS.md (if AI project)
        if project.get("ai_cost_estimate") or tech_stack.get("vector_db") or tech_stack.get("model_provider"):
            ai_doc = self._generate_ai_instructions_doc(project, tech_stack, design)
            result = self.tools.write_file("docs/AI_INSTRUCTIONS.md", ai_doc)
            if result.get("success"):
                self.files_created += 1

        console.print(f"[green]✓[/green] Documentation created")

    def _generate_readme(self, project: Dict, tech_stack: Dict) -> str:
        """Generate README.md."""
        name = project.get("project_name", "My Project")
        concept = project.get("core_concept", "A project built with BOTUVIC")
        features = project.get("features", [])

        features_md = "\n".join([f"- {f}" for f in features]) if features else "- Core functionality"

        return f"""# {name}

{concept}

## Features

{features_md}

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Documentation

- [Setup Guide](docs/SETUP.md)
- [Development Roadmap](docs/ROADMAP.md)

## Built With

- BOTUVIC - AI Project Builder

## License

MIT
"""

    def _generate_setup_doc(self, project: Dict, tech_stack: Dict) -> str:
        """Generate SETUP.md."""
        db = tech_stack.get("database", {})
        provider = db.get("provider", "").lower()

        db_setup = ""
        if "supabase" in provider:
            db_setup = """
## Database Setup (Supabase)

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Go to SQL Editor
4. Copy contents of `../database/schema.sql`
5. Paste and run in SQL Editor
6. Go to Settings > API
7. Copy URL and keys to `.env.local`
"""
        else:
            db_setup = """
## Database Setup

1. Create a PostgreSQL database
2. Run the schema: `psql -d yourdb -f database/schema.sql`
3. Update DATABASE_URL in `.env.local`
"""

        return f"""# Setup Guide

## Prerequisites

- Node.js 18+
- npm or yarn
- Git

## Step 1: Install Dependencies

```bash
cd frontend
npm install
```

## Step 2: Environment Variables

```bash
cp .env.example .env.local
```

Fill in your values in `.env.local`
{db_setup}

## Step 3: Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Step 4: Verify Setup

- [ ] Homepage loads without errors
- [ ] Can navigate to login page
- [ ] Database connection works

## Troubleshooting

### "Module not found"
Run `npm install` again

### Database connection errors
Check your `.env.local` credentials
"""

    def _generate_roadmap_doc(self, project: Dict, design: Dict) -> str:
        """Generate comprehensive ROADMAP.md with phases, tasks, and plan."""
        name = project.get("project_name", "My Project")
        features = project.get("features", [])
        features_tasks = "\n".join([f"- [ ] {f}" for f in features]) if features else "- [ ] Core feature 1\n- [ ] Core feature 2"
        
        # Get data entities for database tasks
        entities = project.get("data_entities", [])
        entity_tasks = "\n".join([f"- [ ] CRUD for {e}" for e in entities]) if entities else "- [ ] CRUD operations"
        
        # Get backend logic if available
        backend_logic = design.get("backend_logic", {}) if design else {}
        routes = backend_logic.get("core_routes", [])
        routes_tasks = "\n".join([f"- [ ] Implement: {r}" for r in routes[:5]]) if routes else "- [ ] API endpoints"

        return f"""# Development Roadmap: {name}

## Overview

This roadmap outlines the development phases, tasks, and milestones for {name}.

---

## 📋 PHASE 1: Foundation ✅ DONE BY BOTUVIC

**Status:** Complete  
**Duration:** Automated

- [x] Project folder structure created
- [x] Database schema designed (`database/schema.sql`)
- [x] Configuration files generated
- [x] Skeleton components created
- [x] Documentation initialized

---

## 🔐 PHASE 2: Authentication & Security

**Status:** Not Started  
**Estimated:** 1-2 days

### Tasks:
- [ ] Implement user signup flow
- [ ] Implement user login flow
- [ ] Add JWT token handling
- [ ] Create auth middleware
- [ ] Protect private routes
- [ ] Add session management
- [ ] Implement logout functionality

### Acceptance Criteria:
- [ ] User can register with email/password
- [ ] User can log in and receive token
- [ ] Protected routes redirect unauthenticated users
- [ ] Tokens refresh properly

---

## ⚡ PHASE 3: Core Features

**Status:** Not Started  
**Estimated:** 3-5 days

### Primary Features (MVP):
{features_tasks}

### Database Operations:
{entity_tasks}

### API Endpoints:
{routes_tasks}

### Acceptance Criteria:
- [ ] All primary features functional
- [ ] Data persists to database
- [ ] API responses are correct

---

## 🎨 PHASE 4: UI/UX Polish

**Status:** Not Started  
**Estimated:** 2-3 days

### Tasks:
- [ ] Add loading states (skeletons, spinners)
- [ ] Implement error boundaries
- [ ] Add success/error toast notifications
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Accessibility audit (a11y)
- [ ] Form validation with error messages
- [ ] Optimistic UI updates

### Optional:
- [ ] Dark mode toggle
- [ ] Animation/transitions
- [ ] Custom 404/500 pages

---

## 🧪 PHASE 5: Testing

**Status:** Not Started  
**Estimated:** 2-3 days

See [TESTING.md](./TESTING.md) for detailed testing plan.

### Unit Tests:
- [ ] Component tests
- [ ] Utility function tests
- [ ] Hook tests

### Integration Tests:
- [ ] API endpoint tests
- [ ] Database operation tests
- [ ] Auth flow tests

### E2E Tests:
- [ ] User signup flow
- [ ] User login flow
- [ ] Main user journey

---

## 🚀 PHASE 6: Deployment

**Status:** Not Started  
**Estimated:** 1 day

### Pre-deployment:
- [ ] Environment variables set
- [ ] Build succeeds locally
- [ ] All tests pass

### Deployment:
- [ ] Push to GitHub
- [ ] Deploy frontend (Vercel/Netlify)
- [ ] Deploy backend (if separate)
- [ ] Configure custom domain (optional)
- [ ] Set up CI/CD (optional)

### Post-deployment:
- [ ] Verify production build works
- [ ] Test all features in production
- [ ] Monitor for errors

---

## 📊 Progress Tracker

| Phase | Status | Progress |
|-------|--------|----------|
| 1. Foundation | ✅ Done | 100% |
| 2. Authentication | 🔲 Not Started | 0% |
| 3. Core Features | 🔲 Not Started | 0% |
| 4. UI/UX Polish | 🔲 Not Started | 0% |
| 5. Testing | 🔲 Not Started | 0% |
| 6. Deployment | 🔲 Not Started | 0% |

---

## 📅 Suggested Timeline

- **Week 1:** Phase 2 (Auth) + Start Phase 3
- **Week 2:** Complete Phase 3 + Phase 4
- **Week 3:** Phase 5 (Testing) + Phase 6 (Deploy)

---

Generated by BOTUVIC CodeAgent
"""

    def _generate_testing_doc(self, project: Dict, tech_stack: Dict) -> str:
        """Generate TESTING.md with testing plan."""
        name = project.get("project_name", "My Project")
        
        # Detect testing framework based on tech stack
        frontend = tech_stack.get("frontends", {}).get("web", "") or tech_stack.get("frontend", {}).get("framework", "")
        backend = tech_stack.get("backend", {})
        backend_lang = backend.get("language", "") if isinstance(backend, dict) else ""
        
        frontend_tests = ""
        if "next" in frontend.lower() or "react" in frontend.lower():
            frontend_tests = """### Frontend Testing (React/Next.js)

**Framework:** Jest + React Testing Library

```bash
# Install testing dependencies
npm install --save-dev jest @testing-library/react @testing-library/jest-dom

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

**Example Component Test:**
```tsx
import { render, screen } from '@testing-library/react'
import HomePage from '@/app/page'

describe('HomePage', () => {
  it('renders welcome message', () => {
    render(<HomePage />)
    expect(screen.getByText(/welcome/i)).toBeInTheDocument()
  })
})
```
"""
        
        backend_tests = ""
        if "python" in backend_lang.lower() or "fastapi" in str(backend).lower():
            backend_tests = """### Backend Testing (Python/FastAPI)

**Framework:** pytest + pytest-asyncio

```bash
# Install testing dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

**Example API Test:**
```python
from httpx import AsyncClient
from app.main import app

async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
```
"""
        
        return f"""# Testing Plan: {name}

## Overview

This document outlines the testing strategy for {name}.

---

## Testing Pyramid

```
        /\\
       /  \\     E2E Tests (10%)
      /----\\    - Full user flows
     /      \\   
    /--------\\  Integration Tests (30%)
   /          \\ - API tests, DB tests
  /------------\\ 
 /              \\ Unit Tests (60%)
/________________\\ - Components, functions
```

---

{frontend_tests}

{backend_tests}

---

## Test Categories

### 1. Unit Tests

Test individual components and functions in isolation.

**What to test:**
- Components render correctly
- Utility functions return expected values
- Hooks work as expected
- State management actions

**Coverage target:** 80%+

---

### 2. Integration Tests

Test how multiple units work together.

**What to test:**
- API endpoints respond correctly
- Database operations work
- Authentication flows
- Form submissions

**Coverage target:** 70%+

---

### 3. End-to-End (E2E) Tests

Test complete user journeys.

**Framework:** Playwright or Cypress

```bash
# Install Playwright
npm init playwright@latest

# Run E2E tests
npx playwright test
```

**Key Flows to Test:**
- [ ] User can sign up
- [ ] User can log in
- [ ] User can complete main task
- [ ] User can log out

---

## Test Coverage Goals

| Type | Target | Priority |
|------|--------|----------|
| Unit | 80% | High |
| Integration | 70% | High |
| E2E | 50% | Medium |

---

## Running Tests

### All Tests
```bash
npm test
```

### With Coverage Report
```bash
npm test -- --coverage
```

### Watch Mode (Development)
```bash
npm test -- --watch
```

### E2E Tests
```bash
npx playwright test
```

---

## CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: npm ci
      - run: npm test -- --coverage
```

---

Generated by BOTUVIC CodeAgent
"""

    def _generate_api_doc(self, project: Dict, design: Dict) -> str:
        """Generate API.md documentation."""
        name = project.get("project_name", "My Project")
        
        # Get routes from design
        backend_logic = design.get("backend_logic", {}) if design else {}
        routes = backend_logic.get("core_routes", [])
        
        routes_doc = ""
        for route in routes[:10]:
            routes_doc += f"\n### `{route}`\n\n**Description:** TODO\n\n**Response:**\n```json\n{{}}\n```\n\n---\n"
        
        if not routes_doc:
            routes_doc = """
### `GET /api/health`

**Description:** Health check endpoint

**Response:**
```json
{
  "status": "healthy"
}
```

---

### `POST /api/auth/login`

**Description:** User authentication

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}
```

---

### `GET /api/users/me`

**Description:** Get current user profile

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "created_at": "2024-01-01T00:00:00Z"
}
```
"""
        
        return f"""# API Documentation: {name}

## Base URL

- **Development:** `http://localhost:3001/api`
- **Production:** `https://your-domain.com/api`

---

## Authentication

Most endpoints require authentication via JWT token.

**Header:**
```
Authorization: Bearer <access_token>
```

---

## Endpoints

{routes_doc}

---

## Error Responses

All errors follow this format:

```json
{{
  "error": {{
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }}
}}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid input data |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Rate Limiting

- **Limit:** 100 requests per minute
- **Headers:**
  - `X-RateLimit-Limit`: Max requests
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

---

Generated by BOTUVIC CodeAgent
"""

    def _generate_ai_instructions_doc(self, project: Dict, tech_stack: Dict, design: Dict) -> str:
        """Generate AI_INSTRUCTIONS.md for AI projects."""
        name = project.get("project_name", "My Project")
        
        vector_db = tech_stack.get("vector_db", "Not specified")
        model_provider = tech_stack.get("model_provider", "OpenAI")
        ai_cost = project.get("ai_cost_estimate", "Not calculated")
        
        # Get AI pipeline from design
        backend_logic = design.get("backend_logic", {}) if design else {}
        ai_pipeline = backend_logic.get("ai_rag_pipeline", {})
        
        pipeline_flow = ai_pipeline.get("flow", "User Input → Embedding → Vector Search → LLM Synthesis → Output") if isinstance(ai_pipeline, dict) else "User Input → Embedding → Vector Search → LLM Synthesis → Output"
        system_prompt = ai_pipeline.get("system_prompt_structure", "Not defined") if isinstance(ai_pipeline, dict) else "Not defined"
        
        return f"""# AI Instructions: {name}

## Overview

This document outlines the AI architecture, prompts, and implementation details for {name}.

---

## AI Stack

| Component | Technology |
|-----------|------------|
| **Vector Database** | {vector_db} |
| **LLM Provider** | {model_provider} |
| **Estimated Cost** | {ai_cost} |

---

## RAG Pipeline Architecture

```
{pipeline_flow}
```

### Detailed Flow:

1. **User Input**
   - Receive user query
   - Clean and preprocess text
   - Log for analytics

2. **Embedding Generation**
   - Convert query to vector embedding
   - Model: `text-embedding-ada-002` (or similar)
   - Dimensions: 1536

3. **Vector Search (RAG)**
   - Search vector database for relevant context
   - Top K: 5 results
   - Similarity threshold: 0.7

4. **Context Assembly**
   - Combine search results into context
   - Truncate if over token limit
   - Format for LLM

5. **LLM Synthesis**
   - Send context + query to LLM
   - Apply system prompt
   - Generate response

6. **Output**
   - Stream or return response
   - Log for analytics
   - Store in chat history

---

## System Prompt Structure

```
{system_prompt}
```

### Template:

```python
SYSTEM_PROMPT = \"\"\"
You are {name}'s AI assistant.

## Your Role
- Help users with [specific task]
- Use the provided context to answer questions
- Be concise and accurate

## Rules
1. Only answer based on the provided context
2. If unsure, say "I don't have enough information"
3. Never make up facts
4. Cite sources when possible

## Context
{{context}}

## User Query
{{query}}
\"\"\"
```

---

## Token & Cost Management

### Estimated Costs (based on Phase 1):

{ai_cost}

### Token Limits:

| Component | Max Tokens |
|-----------|------------|
| Context | 3,000 |
| User Input | 500 |
| Response | 1,000 |
| Total | 4,500 |

### Cost Optimization:

- [ ] Cache frequently asked queries
- [ ] Use smaller model for simple queries
- [ ] Implement rate limiting per user
- [ ] Monitor token usage daily

---

## Vector Database Schema

```sql
-- Vectors table
CREATE TABLE vectors (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat history table
CREATE TABLE chat_history (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    tokens_used INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Implementation Checklist

### Setup:
- [ ] Set up vector database ({vector_db})
- [ ] Configure LLM provider ({model_provider})
- [ ] Set API keys in environment

### Embedding Pipeline:
- [ ] Create embedding function
- [ ] Set up document chunking
- [ ] Implement batch embedding

### Search:
- [ ] Implement vector similarity search
- [ ] Add metadata filtering
- [ ] Configure search parameters

### Generation:
- [ ] Create prompt templates
- [ ] Implement streaming (optional)
- [ ] Add response caching

### Monitoring:
- [ ] Log all queries/responses
- [ ] Track token usage
- [ ] Monitor response quality

---

## Environment Variables

```bash
# LLM Provider
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...

# Vector Database
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...
# or
SUPABASE_URL=...
SUPABASE_KEY=...

# Optional: Cost Alerts
COST_ALERT_THRESHOLD=100
DAILY_TOKEN_LIMIT=1000000
```

---

Generated by BOTUVIC CodeAgent
"""

    # =========================================================================
    # STEP 7: INSTALL DEPENDENCIES
    # =========================================================================

    def _step_7_install_dependencies(self, tech_stack: Dict):
        """Install project dependencies with user permission."""
        console.print("[dim]Step 7: Installing dependencies...[/dim]")

        frontend = tech_stack.get("frontend", {}).get("framework", "")
        frontends = tech_stack.get("frontends", {})
        backend = tech_stack.get("backend", {})

        # Install frontend dependencies
        web_framework = frontends.get("web", frontend)
        if web_framework and ("next" in web_framework.lower() or "react" in web_framework.lower() or "vue" in web_framework.lower()):
            frontend_path = os.path.join(self.project_dir, "frontend")
            if os.path.exists(os.path.join(frontend_path, "package.json")):
                result = self.tools.run_command(
                    "npm install",
                    description="Install frontend Node.js dependencies",
                    working_dir=frontend_path
                )
                if result.get("success"):
                    console.print("[green]✓[/green] Frontend dependencies installed")
                elif result.get("skipped"):
                    console.print("[dim]Skipped frontend dependencies[/dim]")

        # Install backend dependencies
        backend_lang = backend.get("language", "") if isinstance(backend, dict) else ""
        if "python" in backend_lang.lower():
            backend_path = os.path.join(self.project_dir, "backend")
            if os.path.exists(os.path.join(backend_path, "requirements.txt")):
                result = self.tools.run_command(
                    "pip install -r requirements.txt",
                    description="Install backend Python dependencies",
                    working_dir=backend_path
                )
                if result.get("success"):
                    console.print("[green]✓[/green] Backend dependencies installed")
                elif result.get("skipped"):
                    console.print("[dim]Skipped backend dependencies[/dim]")

        console.print("[green]✓[/green] Dependency installation complete")

    # =========================================================================
    # STEP 8: VERIFICATION
    # =========================================================================

    def _step_8_verification(self, tech_stack: Dict) -> Dict[str, Any]:
        """Verify project structure."""
        console.print("[dim]Step 8: Verifying project...[/dim]")

        backend_needed = tech_stack.get("backend_needed", True)
        
        checks = {
            "gitignore": self.tools.file_exists(".gitignore"),
            "readme": self.tools.file_exists("README.md"),
            "setup_doc": self.tools.file_exists("docs/SETUP.md")
        }
        
        # Frontend checks (check for any frontend)
        frontends = tech_stack.get("frontends", {})
        if frontends.get("web"):
            checks["package_json"] = self.tools.file_exists("frontend/package.json")
            # Check for Next.js or React files
            checks["frontend_layout"] = (
                self.tools.file_exists("frontend/src/app/layout.tsx") or
                self.tools.file_exists("frontend/src/App.tsx") or
                self.tools.file_exists("frontend/src/App.vue")
            )
        
        # Backend checks (only if backend needed)
        if backend_needed:
            checks["database_schema"] = self.tools.file_exists("database/schema.sql")
            # Check for backend files
            backend = tech_stack.get("backend", {})
            if isinstance(backend, dict):
                backend_lang = backend.get("language", "").lower()
                if "python" in backend_lang:
                    checks["backend_main"] = self.tools.file_exists("backend/app/main.py")
                elif "node" in backend_lang or "javascript" in backend_lang:
                    checks["backend_main"] = self.tools.file_exists("backend/src/index.js")
                elif "go" in backend_lang:
                    checks["backend_main"] = self.tools.file_exists("backend/cmd/server/main.go")
        
        # Environment example (optional)
        checks["env_example"] = self.tools.file_exists(".env.example")

        passed = sum(checks.values())
        total = len(checks)

        console.print(f"[green]✓[/green] Verification: {passed}/{total} checks passed")

        return {
            "checks": checks,
            "passed": passed,
            "total": total,
            "ready": passed == total
        }

    def _get_next_steps(self, tech_stack: Dict) -> str:
        """Get next steps message."""
        backend_needed = tech_stack.get("backend_needed", True)
        frontends = tech_stack.get("frontends", {})
        
        steps = []
        
        # Frontend steps
        if frontends.get("web"):
            steps.append("1. cd frontend && npm install")
            steps.append("2. Copy .env.example to .env.local (if exists)")
            steps.append("3. npm run dev")
        elif frontends.get("mobile"):
            if "flutter" in frontends.get("mobile", "").lower():
                steps.append("1. cd mobile && flutter pub get")
                steps.append("2. flutter run")
            elif "react native" in frontends.get("mobile", "").lower() or "expo" in frontends.get("mobile", "").lower():
                steps.append("1. cd mobile && npm install")
                steps.append("2. npm start")
        
        # Backend steps (only if needed)
        if backend_needed:
            db_provider = tech_stack.get("database", {}).get("provider", "").lower()
            if "supabase" in db_provider:
                steps.append("4. Create Supabase project and copy credentials")
                steps.append("5. Run database/schema.sql in Supabase SQL Editor")
            elif db_provider:
                steps.append("4. Set up your database")
                steps.append("5. Run database/schema.sql")
            
            backend = tech_stack.get("backend", {})
            if isinstance(backend, dict):
                backend_lang = backend.get("language", "").lower()
                if "python" in backend_lang:
                    steps.append("6. cd backend && pip install -r requirements.txt")
                    steps.append("7. uvicorn app.main:app --reload")
                elif "node" in backend_lang or "javascript" in backend_lang:
                    steps.append("6. cd backend && npm install")
                    steps.append("7. npm run dev")
                elif "go" in backend_lang:
                    steps.append("6. cd backend && go mod download")
                    steps.append("7. go run cmd/server/main.go")

        return "\n".join(steps) if steps else "Check README.md for setup instructions"
