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

            # Step 2: Database setup
            self._update_todo(2, "in_progress")
            self._step_2_database_setup(design, tech_stack)
            self._update_todo(2, "complete")

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

            # Step 7: Install dependencies (optional)
            # self._step_7_install_dependencies(tech_stack)

            # Step 8: Final verification
            verification = self._step_8_verification()

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

        frontend = tech_stack.get("frontend", {})
        framework = frontend.get("framework", "Next.js")

        if "next" in framework.lower():
            self._create_nextjs_skeletons(project, tech_stack, design)

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
    # STEP 6: DOCUMENTATION
    # =========================================================================

    def _step_6_documentation(self, project: Dict, tech_stack: Dict, design: Dict):
        """Generate documentation files."""
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

        # docs/ROADMAP.md
        roadmap = self._generate_roadmap_doc(project)
        result = self.tools.write_file("docs/ROADMAP.md", roadmap)
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

    def _generate_roadmap_doc(self, project: Dict) -> str:
        """Generate ROADMAP.md."""
        return """# Development Roadmap

## Phase 1: Setup ✅ DONE BY BOTUVIC

- [x] Project structure created
- [x] Database schema ready
- [x] Configuration files set
- [x] Base components created

## Phase 2: Authentication

- [ ] Implement signup flow
- [ ] Implement login flow
- [ ] Add auth middleware
- [ ] Protect dashboard routes

## Phase 3: Core Features

- [ ] Build main dashboard
- [ ] Implement CRUD operations
- [ ] Add form validation
- [ ] Connect to database

## Phase 4: Polish

- [ ] Loading states
- [ ] Error handling
- [ ] Responsive design
- [ ] Dark mode (optional)

## Phase 5: Testing

- [ ] Unit tests
- [ ] Integration tests
- [ ] E2E tests

## Phase 6: Deployment

- [ ] Push to GitHub
- [ ] Deploy to Vercel/hosting
- [ ] Set production env vars
- [ ] Test production build

---

Generated by BOTUVIC
"""

    # =========================================================================
    # STEP 8: VERIFICATION
    # =========================================================================

    def _step_8_verification(self) -> Dict[str, Any]:
        """Verify project structure."""
        console.print("[dim]Step 8: Verifying project...[/dim]")

        checks = {
            "database_schema": self.tools.file_exists("database/schema.sql"),
            "package_json": self.tools.file_exists("frontend/package.json"),
            "layout": self.tools.file_exists("frontend/src/app/layout.tsx"),
            "home_page": self.tools.file_exists("frontend/src/app/page.tsx"),
            "gitignore": self.tools.file_exists(".gitignore"),
            "env_example": self.tools.file_exists(".env.example"),
            "readme": self.tools.file_exists("README.md"),
            "setup_doc": self.tools.file_exists("docs/SETUP.md")
        }

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
        db_provider = tech_stack.get("database", {}).get("provider", "").lower()

        steps = ["1. cd frontend && npm install"]

        if "supabase" in db_provider:
            steps.append("2. Create Supabase project and copy credentials")
            steps.append("3. Run schema.sql in Supabase SQL Editor")
        else:
            steps.append("2. Set up your database")
            steps.append("3. Run database/schema.sql")

        steps.append("4. Copy .env.example to .env.local")
        steps.append("5. npm run dev")

        return "\n".join(steps)
