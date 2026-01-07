"""
Database Setup Module for BOTUVIC.
Handles 100% database setup for ANY database type (SQL and NoSQL).
"""

import os
import json
import re
import subprocess
from typing import Dict, Any, List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


class DatabaseSetup:
    """Universal database setup handler."""

    def __init__(self, project_dir: str, storage):
        self.project_dir = project_dir
        self.storage = storage

    def setup_database(self) -> Dict[str, Any]:
        """
        Main function to setup database 100%.

        Returns:
            Dict with success status, db_type, tables_created, etc.
        """
        # Load tech stack and schema (try multiple sources)
        project = self.storage.load("project") or {}
        tech_stack = self.storage.load("tech_stack") or project.get("tech_stack", {})
        database_info = tech_stack.get("database", {})

        if not database_info:
            # Also try loading from project_info
            project_info = self.storage.load("project_info") or {}
            tech_stack = project_info.get("tech_stack", {})
            database_info = tech_stack.get("database", {})

        if not database_info:
            return {"success": False, "error": "No database configured"}

        db_name = database_info.get("name", "").lower()
        db_type = self._detect_db_type(db_name)

        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Detected database:[/#F1F5F9] {db_name} ({db_type})")

        # Load schema from Phase 3
        database_schema = self.storage.load("database_schema") or {}

        if not database_schema:
            return {"success": False, "error": "No database schema found (Phase 3)"}

        # Generate schema files based on DB type
        if db_type == "sql":
            result = self._setup_sql_database(db_name, database_schema)
        elif db_type == "nosql":
            result = self._setup_nosql_database(db_name, database_schema)
        else:
            return {"success": False, "error": f"Unsupported database type: {db_type}"}

        return result

    def _detect_db_type(self, db_name: str) -> str:
        """Detect if database is SQL or NoSQL."""
        sql_databases = ["postgresql", "postgres", "mysql", "sqlite", "supabase", "planetscale", "mariadb", "cockroachdb"]
        nosql_databases = ["mongodb", "mongo", "firebase", "firestore", "dynamodb", "redis", "cassandra"]

        for sql_db in sql_databases:
            if sql_db in db_name:
                return "sql"

        for nosql_db in nosql_databases:
            if nosql_db in db_name:
                return "nosql"

        # Default to SQL if unknown
        return "sql"

    def _setup_sql_database(self, db_name: str, schema: Dict) -> Dict[str, Any]:
        """Setup SQL database (PostgreSQL, MySQL, SQLite, etc.)."""

        # Detect specific SQL dialect
        dialect = self._get_sql_dialect(db_name)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]SQL dialect:[/#F1F5F9] {dialect}")

        # Generate SQL schema
        generator = SQLSchemaGenerator(dialect, self.project_dir)
        sql_content, tables = generator.generate_schema(schema)

        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Generating SQL schema...[/#F1F5F9] ✓")

        # Write schema.sql
        schema_path = os.path.join(self.project_dir, "database", "schema.sql")
        os.makedirs(os.path.dirname(schema_path), exist_ok=True)
        with open(schema_path, 'w') as f:
            f.write(sql_content)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] database/schema.sql ✓")

        # Write migration file
        migration_path = os.path.join(self.project_dir, "database", "migrations", "001_initial_schema.sql")
        os.makedirs(os.path.dirname(migration_path), exist_ok=True)
        with open(migration_path, 'w') as f:
            f.write(sql_content)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] database/migrations/001_initial_schema.sql ✓")

        # Create connection config
        conn_config = self._create_sql_connection_config(db_name, dialect)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created connection config[/#F1F5F9] ✓")

        # Create README with instructions
        readme_content = self._create_db_readme(db_name, dialect, tables)
        readme_path = os.path.join(self.project_dir, "database", "README.md")
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] database/README.md ✓")

        console.print(f"[#10B981]✓ Database setup complete! {len(tables)} tables ready.[/#10B981]")

        return {
            "success": True,
            "db_type": db_name,
            "dialect": dialect,
            "tables_created": tables,
            "files_created": [
                "database/schema.sql",
                "database/migrations/001_initial_schema.sql",
                "backend/src/config/database.js",
                "database/README.md"
            ]
        }

    def _setup_nosql_database(self, db_name: str, schema: Dict) -> Dict[str, Any]:
        """Setup NoSQL database (MongoDB, Firebase, etc.)."""

        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Setting up NoSQL database...[/#F1F5F9]")

        # Generate NoSQL schema
        generator = NoSQLSchemaGenerator(db_name, self.project_dir)
        schema_content, collections = generator.generate_schema(schema)

        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Generating NoSQL schema...[/#F1F5F9] ✓")

        # Write schema file (JSON for MongoDB, rules for Firebase)
        if "mongo" in db_name:
            schema_path = os.path.join(self.project_dir, "database", "schema.json")
            os.makedirs(os.path.dirname(schema_path), exist_ok=True)
            with open(schema_path, 'w') as f:
                f.write(json.dumps(schema_content, indent=2))
            console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] database/schema.json ✓")

        elif "firebase" in db_name or "firestore" in db_name:
            # Firestore rules
            rules_path = os.path.join(self.project_dir, "database", "firestore.rules")
            os.makedirs(os.path.dirname(rules_path), exist_ok=True)
            with open(rules_path, 'w') as f:
                f.write(schema_content)
            console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] database/firestore.rules ✓")

            # Also create indexes
            indexes_path = os.path.join(self.project_dir, "database", "firestore.indexes.json")
            indexes = generator.generate_indexes(schema)
            with open(indexes_path, 'w') as f:
                f.write(json.dumps(indexes, indent=2))
            console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] database/firestore.indexes.json ✓")

        # Create connection config
        conn_config = self._create_nosql_connection_config(db_name)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created connection config[/#F1F5F9] ✓")

        # Create README with instructions
        readme_content = self._create_nosql_readme(db_name, collections)
        readme_path = os.path.join(self.project_dir, "database", "README.md")
        os.makedirs(os.path.dirname(readme_path), exist_ok=True)
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        console.print(f"[#A855F7]⏺[/#A855F7] [#F1F5F9]Created:[/#F1F5F9] database/README.md ✓")

        console.print(f"[#10B981]✓ Database setup complete! {len(collections)} collections ready.[/#10B981]")

        return {
            "success": True,
            "db_type": db_name,
            "collections_created": collections,
            "files_created": [
                "database/schema.json" if "mongo" in db_name else "database/firestore.rules",
                "backend/src/config/database.js",
                "database/README.md"
            ]
        }

    def _get_sql_dialect(self, db_name: str) -> str:
        """Get specific SQL dialect."""
        if "postgres" in db_name or "supabase" in db_name:
            return "postgresql"
        elif "mysql" in db_name or "planetscale" in db_name or "mariadb" in db_name:
            return "mysql"
        elif "sqlite" in db_name:
            return "sqlite"
        else:
            return "postgresql"  # Default

    def _create_sql_connection_config(self, db_name: str, dialect: str) -> str:
        """Create database connection config file for backend."""

        backend_path = os.path.join(self.project_dir, "backend", "src", "config")
        os.makedirs(backend_path, exist_ok=True)

        if "supabase" in db_name:
            config_content = """import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_SERVICE_KEY

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Missing Supabase credentials in .env file')
}

export const supabase = createClient(supabaseUrl, supabaseKey)

// Test connection
export async function testConnection() {
  try {
    const { data, error } = await supabase.from('users').select('count', { count: 'exact', head: true })
    if (error) throw error
    console.log('✓ Database connected successfully')
    return true
  } catch (err) {
    console.error('✗ Database connection failed:', err.message)
    return false
  }
}
"""
        elif dialect == "postgresql":
            config_content = """import pkg from 'pg'
const { Pool } = pkg

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
})

// Test connection
pool.on('connect', () => {
  console.log('✓ Database connected successfully')
})

pool.on('error', (err) => {
  console.error('✗ Database connection error:', err)
})

export default pool
"""
        elif dialect == "mysql":
            config_content = """import mysql from 'mysql2/promise'

export const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
})

// Test connection
export async function testConnection() {
  try {
    const connection = await pool.getConnection()
    console.log('✓ Database connected successfully')
    connection.release()
    return true
  } catch (err) {
    console.error('✗ Database connection failed:', err.message)
    return false
  }
}
"""
        elif dialect == "sqlite":
            config_content = """import sqlite3 from 'sqlite3'
import { open } from 'sqlite'

let db = null

export async function getDatabase() {
  if (db) return db

  db = await open({
    filename: process.env.DB_PATH || './database.sqlite',
    driver: sqlite3.Database
  })

  console.log('✓ Database connected successfully')
  return db
}

export default getDatabase
"""
        else:
            config_content = "// Database connection config\n"

        config_path = os.path.join(backend_path, "database.js")
        with open(config_path, 'w') as f:
            f.write(config_content)

        return config_path

    def _create_nosql_connection_config(self, db_name: str) -> str:
        """Create NoSQL database connection config."""

        backend_path = os.path.join(self.project_dir, "backend", "src", "config")
        os.makedirs(backend_path, exist_ok=True)

        if "mongo" in db_name:
            config_content = """import { MongoClient } from 'mongodb'

const uri = process.env.MONGODB_URI

if (!uri) {
  throw new Error('Missing MONGODB_URI in .env file')
}

const client = new MongoClient(uri)

let db = null

export async function connectDB() {
  if (db) return db

  try {
    await client.connect()
    db = client.db(process.env.DB_NAME || 'myapp')
    console.log('✓ MongoDB connected successfully')
    return db
  } catch (err) {
    console.error('✗ MongoDB connection failed:', err.message)
    throw err
  }
}

export async function getDB() {
  if (!db) {
    await connectDB()
  }
  return db
}

export default { connectDB, getDB }
"""
        elif "firebase" in db_name or "firestore" in db_name:
            config_content = """import admin from 'firebase-admin'

// Initialize Firebase Admin SDK
if (!admin.apps.length) {
  admin.initializeApp({
    credential: admin.credential.cert({
      projectId: process.env.FIREBASE_PROJECT_ID,
      clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
      privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\\\n/g, '\\n')
    })
  })
}

export const db = admin.firestore()
export const auth = admin.auth()

console.log('✓ Firebase connected successfully')

export default { db, auth }
"""
        else:
            config_content = "// NoSQL database connection config\n"

        config_path = os.path.join(backend_path, "database.js")
        with open(config_path, 'w') as f:
            f.write(config_content)

        return config_path

    def _create_db_readme(self, db_name: str, dialect: str, tables: List[str]) -> str:
        """Create database README with setup instructions."""

        content = f"""# Database Setup - {db_name}

## Schema Overview

This database contains {len(tables)} tables:
"""
        for table in tables:
            content += f"- `{table}`\n"

        content += f"""

## Setup Instructions

### 1. Install Database

"""

        if "supabase" in db_name:
            content += """**Supabase (Recommended)**

1. Go to https://supabase.com
2. Create a new project
3. Copy your project URL and API keys
4. Add to `.env` file:
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
```
"""
        elif dialect == "postgresql":
            content += """**PostgreSQL**

1. Install PostgreSQL: https://www.postgresql.org/download/
2. Create a database:
```bash
createdb myapp_db
```
3. Add connection string to `.env`:
```
DATABASE_URL=postgresql://username:password@localhost:5432/myapp_db
```
"""
        elif dialect == "mysql":
            content += """**MySQL**

1. Install MySQL: https://dev.mysql.com/downloads/
2. Create a database:
```bash
mysql -u root -p
CREATE DATABASE myapp_db;
```
3. Add credentials to `.env`:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=myapp_db
```
"""
        elif dialect == "sqlite":
            content += """**SQLite**

1. SQLite is file-based, no installation needed
2. Add to `.env`:
```
DB_PATH=./database.sqlite
```
"""

        content += """

### 2. Run Migrations

Run the schema to create all tables:

"""

        if "supabase" in db_name:
            content += """1. Go to Supabase Dashboard → SQL Editor
2. Copy contents of `database/schema.sql`
3. Paste and run in SQL Editor
4. All tables will be created
"""
        else:
            content += f"""```bash
# PostgreSQL
psql -d myapp_db -f database/schema.sql

# MySQL
mysql -u root -p myapp_db < database/schema.sql

# SQLite
sqlite3 database.sqlite < database/schema.sql
```
"""

        content += """

### 3. Test Connection

```bash
cd backend
npm install
node -e "import('./src/config/database.js').then(m => m.testConnection?.())"
```

You should see: `✓ Database connected successfully`

### 4. Ready to Code!

Your database is now 100% ready. Backend can connect and start building APIs.

## Schema File

See `database/schema.sql` for the complete database schema with all tables, indexes, and constraints.
"""

        return content

    def _create_nosql_readme(self, db_name: str, collections: List[str]) -> str:
        """Create NoSQL database README."""

        content = f"""# Database Setup - {db_name}

## Schema Overview

This database contains {len(collections)} collections:
"""
        for coll in collections:
            content += f"- `{coll}`\n"

        content += "\n## Setup Instructions\n\n"

        if "mongo" in db_name:
            content += """### MongoDB Setup

1. **Install MongoDB**:
   - Local: https://www.mongodb.com/try/download/community
   - Or use MongoDB Atlas (cloud): https://www.mongodb.com/cloud/atlas

2. **Create Database**:
```bash
# Local MongoDB
mongosh
use myapp_db
```

3. **Add to `.env`**:
```
MONGODB_URI=mongodb://localhost:27017
DB_NAME=myapp_db
```

4. **Create Collections & Indexes**:
```bash
# The schema.json file contains collection definitions
# Collections will be created automatically on first insert
# But you can pre-create them:
node scripts/setup-mongo.js
```

5. **Test Connection**:
```bash
cd backend
npm install
node -e "import('./src/config/database.js').then(m => m.connectDB())"
```
"""
        elif "firebase" in db_name or "firestore" in db_name:
            content += """### Firebase Firestore Setup

1. **Create Firebase Project**:
   - Go to https://console.firebase.google.com
   - Create new project
   - Enable Firestore Database

2. **Get Service Account**:
   - Project Settings → Service Accounts
   - Generate new private key (downloads JSON file)

3. **Add to `.env`**:
```
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\\nYour key here\\n-----END PRIVATE KEY-----\\n"
```

4. **Deploy Security Rules**:
```bash
firebase deploy --only firestore:rules
```

5. **Deploy Indexes**:
```bash
firebase deploy --only firestore:indexes
```

6. **Test Connection**:
```bash
cd backend
npm install
node -e "import('./src/config/database.js')"
```
"""

        content += "\n### Ready to Code!\n\nYour database is now 100% ready. Backend can connect and start building APIs.\n"

        return content

    def auto_setup_database(self, db_name: str, schema_path: str) -> Dict[str, Any]:
        """
        Auto-setup database with user approval.

        For local databases: Runs commands to create DB and apply schema
        For cloud databases: Shows instructions
        """
        # Detect if cloud or local
        is_cloud = any(cloud in db_name for cloud in ["supabase", "firebase", "planetscale"])

        if is_cloud:
            return self._show_cloud_instructions(db_name, schema_path)
        else:
            return self._auto_setup_local_database(db_name, schema_path)

    def _auto_setup_local_database(self, db_name: str, schema_path: str) -> Dict[str, Any]:
        """Auto-setup local database (PostgreSQL, MySQL, MongoDB)."""

        # Detect database type
        if "postgres" in db_name:
            return self._setup_postgresql(schema_path)
        elif "mysql" in db_name:
            return self._setup_mysql(schema_path)
        elif "mongo" in db_name:
            return self._setup_mongodb(schema_path)
        else:
            return {"success": False, "error": "Unknown database type for auto-setup"}

    def _setup_postgresql(self, schema_path: str) -> Dict[str, Any]:
        """Auto-setup PostgreSQL database."""
        project = self.storage.load("project") or {}
        db_config = project.get("database_config", {})
        db_name_value = db_config.get("db_name", "myapp_db")

        console.print("\n[bold cyan]PostgreSQL Auto-Setup[/bold cyan]")
        console.print(f"Database name: {db_name_value}\n")

        # Ask user approval for each command
        commands = [
            {
                "description": f"Create database '{db_name_value}'",
                "command": f"createdb {db_name_value}",
                "required": True
            },
            {
                "description": f"Apply schema from {schema_path}",
                "command": f"psql -d {db_name_value} -f {schema_path}",
                "required": True
            }
        ]

        return self._execute_commands_with_approval(commands, "PostgreSQL")

    def _setup_mysql(self, schema_path: str) -> Dict[str, Any]:
        """Auto-setup MySQL database."""
        project = self.storage.load("project") or {}
        db_config = project.get("database_config", {})
        db_name_value = db_config.get("db_name", "myapp_db")

        console.print("\n[bold cyan]MySQL Auto-Setup[/bold cyan]")
        console.print(f"Database name: {db_name_value}\n")

        commands = [
            {
                "description": f"Create database '{db_name_value}'",
                "command": f"mysql -e 'CREATE DATABASE IF NOT EXISTS {db_name_value};'",
                "required": True
            },
            {
                "description": f"Apply schema from {schema_path}",
                "command": f"mysql {db_name_value} < {schema_path}",
                "required": True
            }
        ]

        return self._execute_commands_with_approval(commands, "MySQL")

    def _setup_mongodb(self, schema_path: str) -> Dict[str, Any]:
        """Auto-setup MongoDB database."""
        console.print("\n[bold cyan]MongoDB Auto-Setup[/bold cyan]")
        console.print("MongoDB doesn't require schema migration for NoSQL.\n")

        # MongoDB doesn't need schema creation, just show connection info
        console.print("[green]✓[/green] MongoDB is ready!")
        console.print(f"Just start your backend and it will auto-create collections.\n")

        return {"success": True, "db_type": "mongodb", "auto_created": True}

    def _execute_commands_with_approval(self, commands: List[Dict], db_type: str) -> Dict[str, Any]:
        """Execute commands with user approval."""
        results = []

        for cmd_info in commands:
            description = cmd_info["description"]
            command = cmd_info["command"]

            # Show command to user
            console.print(f"\n[yellow]Command:[/yellow] {command}")
            console.print(f"[dim]{description}[/dim]")

            # Ask for approval (skip in non-interactive mode or EOF)
            import os
            import sys
            if os.getenv("BOTUVIC_NON_INTERACTIVE", "").lower() == "true" or not sys.stdin.isatty():
                response = "n"  # Skip auto-setup in non-interactive mode
                console.print("[dim]Skipping database auto-setup (non-interactive mode)[/dim]")
            else:
                try:
                    response = console.input("\n[bold]Run this command? (y/n):[/bold] ").strip().lower()
                except EOFError:
                    response = "n"
                    console.print("[dim]Skipping (non-interactive)[/dim]")

            if response == 'y' or response == 'yes':
                try:
                    # Execute command
                    console.print(f"[dim]Running...[/dim]")
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if result.returncode == 0:
                        console.print(f"[green]✓ Success![/green]")
                        results.append({"command": command, "success": True})
                    else:
                        console.print(f"[red]✗ Error:[/red] {result.stderr}")
                        results.append({"command": command, "success": False, "error": result.stderr})

                        if cmd_info.get("required"):
                            console.print("[red]Required command failed. Stopping setup.[/red]")
                            return {"success": False, "db_type": db_type, "results": results}

                except subprocess.TimeoutExpired:
                    console.print("[red]✗ Command timed out[/red]")
                    results.append({"command": command, "success": False, "error": "Timeout"})
                except Exception as e:
                    console.print(f"[red]✗ Error: {str(e)}[/red]")
                    results.append({"command": command, "success": False, "error": str(e)})
            else:
                console.print("[yellow]Skipped[/yellow]")
                results.append({"command": command, "success": False, "skipped": True})

        all_success = all(r.get("success", False) for r in results if not r.get("skipped"))

        if all_success:
            console.print(f"\n[bold green]✓ {db_type} setup complete![/bold green]\n")

        return {"success": all_success, "db_type": db_type, "results": results}

    def _show_cloud_instructions(self, db_name: str, schema_path: str) -> Dict[str, Any]:
        """Show instructions for cloud databases (Supabase, Firebase, etc.)."""

        if "supabase" in db_name:
            return self._show_supabase_instructions(schema_path)
        elif "firebase" in db_name:
            return self._show_firebase_instructions(schema_path)
        elif "planetscale" in db_name:
            return self._show_planetscale_instructions(schema_path)
        else:
            return {"success": True, "message": "Cloud database - manual setup required"}

    def _show_supabase_instructions(self, schema_path: str) -> Dict[str, Any]:
        """Show Supabase setup instructions."""

        with open(schema_path, 'r') as f:
            schema_content = f.read()

        instructions = f"""
# 🚀 Supabase Database Setup

## Step 1: Open Supabase Dashboard
1. Go to: https://supabase.com/dashboard
2. Select your project
3. Click on "SQL Editor" in the left sidebar

## Step 2: Copy & Paste SQL Schema
Copy the SQL below and paste it into the SQL Editor:

```sql
{schema_content}
```

## Step 3: Run the SQL
1. Click "RUN" button in the SQL Editor
2. Wait for success message

## Step 4: Get Your Credentials
1. Go to Project Settings → API
2. Copy these values to your backend `.env` file:
   - SUPABASE_URL
   - SUPABASE_ANON_KEY
   - SUPABASE_SERVICE_KEY

## ✅ Done!
Your Supabase database is now ready!
"""

        panel = Panel(
            Markdown(instructions),
            title="[bold cyan]Supabase Setup Instructions[/bold cyan]",
            border_style="cyan"
        )

        console.print("\n")
        console.print(panel)
        console.print("\n")

        # Save instructions to file
        instructions_path = os.path.join(self.project_dir, "database", "SUPABASE_SETUP.md")
        with open(instructions_path, 'w') as f:
            f.write(instructions)

        console.print(f"[green]✓[/green] Instructions saved to: database/SUPABASE_SETUP.md\n")

        return {"success": True, "db_type": "supabase", "instructions_file": "database/SUPABASE_SETUP.md"}

    def _show_firebase_instructions(self, schema_path: str) -> Dict[str, Any]:
        """Show Firebase setup instructions."""

        instructions = f"""
# 🚀 Firebase Database Setup

## Step 1: Open Firebase Console
1. Go to: https://console.firebase.google.com
2. Select your project
3. Click on "Firestore Database" in the left sidebar

## Step 2: Create Firestore Database
1. Click "Create database"
2. Choose "Start in production mode"
3. Select your region
4. Click "Enable"

## Step 3: Set Up Collections
Your collections will be auto-created when you add data.
Check: database/schema.json for your collection structure

## Step 4: Get Your Credentials
1. Go to Project Settings → Service Accounts
2. Click "Generate new private key"
3. Save the JSON file to your backend folder
4. Add to `.env`:
   - FIREBASE_PROJECT_ID
   - FIREBASE_PRIVATE_KEY
   - FIREBASE_CLIENT_EMAIL

## ✅ Done!
Your Firebase database is now ready!
"""

        panel = Panel(
            Markdown(instructions),
            title="[bold yellow]Firebase Setup Instructions[/bold yellow]",
            border_style="yellow"
        )

        console.print("\n")
        console.print(panel)
        console.print("\n")

        # Save instructions to file
        instructions_path = os.path.join(self.project_dir, "database", "FIREBASE_SETUP.md")
        with open(instructions_path, 'w') as f:
            f.write(instructions)

        console.print(f"[green]✓[/green] Instructions saved to: database/FIREBASE_SETUP.md\n")

        return {"success": True, "db_type": "firebase", "instructions_file": "database/FIREBASE_SETUP.md"}

    def _show_planetscale_instructions(self, schema_path: str) -> Dict[str, Any]:
        """Show PlanetScale setup instructions."""

        with open(schema_path, 'r') as f:
            schema_content = f.read()

        instructions = f"""
# 🚀 PlanetScale Database Setup

## Step 1: Open PlanetScale Dashboard
1. Go to: https://app.planetscale.com
2. Select your database
3. Go to "Console" tab

## Step 2: Apply Schema
Copy and paste this SQL:

```sql
{schema_content}
```

## Step 3: Get Connection String
1. Go to "Connect" tab
2. Copy the connection string
3. Add to your `.env` file

## ✅ Done!
Your PlanetScale database is ready!
"""

        panel = Panel(
            Markdown(instructions),
            title="[bold magenta]PlanetScale Setup Instructions[/bold magenta]",
            border_style="magenta"
        )

        console.print("\n")
        console.print(panel)
        console.print("\n")

        # Save instructions to file
        instructions_path = os.path.join(self.project_dir, "database", "PLANETSCALE_SETUP.md")
        with open(instructions_path, 'w') as f:
            f.write(instructions)

        console.print(f"[green]✓[/green] Instructions saved to: database/PLANETSCALE_SETUP.md\n")

        return {"success": True, "db_type": "planetscale", "instructions_file": "database/PLANETSCALE_SETUP.md"}


class SQLSchemaGenerator:
    """Generate SQL schema for any SQL dialect."""

    def __init__(self, dialect: str, project_dir: str):
        self.dialect = dialect
        self.project_dir = project_dir

    def generate_schema(self, schema: Dict) -> Tuple[str, List[str]]:
        """
        Generate SQL schema from Phase 3 database schema.

        Returns:
            Tuple of (sql_content, table_names)
        """
        tables = schema.get("tables", [])
        relationships = schema.get("relationships", [])

        sql_lines = []
        sql_lines.append(f"-- Database Schema")
        sql_lines.append(f"-- Generated by BOTUVIC")
        sql_lines.append(f"-- Dialect: {self.dialect}")
        sql_lines.append("")

        table_names = []

        for table in tables:
            # Handle both string and dict formats
            if isinstance(table, str):
                # Simple string format: just table name
                table_name = table
                fields = []
                indexes = []
            else:
                # Dict format with full details
                table_name = table.get("name", "")
                # Support both "columns" (new format) and "fields" (old format)
                fields = table.get("columns", []) or table.get("fields", [])
                indexes = table.get("indexes", [])

            table_names.append(table_name)

            sql_lines.append(f"-- Table: {table_name}")
            sql_lines.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")

            field_defs = []
            for field in fields:
                field_def = self._generate_field(field)
                field_defs.append(f"  {field_def}")

            sql_lines.append(",\n".join(field_defs))
            sql_lines.append(");")
            sql_lines.append("")

            # Add indexes
            for idx in indexes:
                idx_sql = self._generate_index(table_name, idx)
                sql_lines.append(idx_sql)

            sql_lines.append("")

        return "\n".join(sql_lines), table_names

    def _sanitize_constraints(self, constraints: str) -> str:
        """Sanitize constraints string to produce valid SQL syntax."""
        import re

        original = constraints

        # Fix 1: Remove "FOREIGN KEY" before REFERENCES (PostgreSQL inline FK is just REFERENCES)
        constraints = re.sub(r'\bFOREIGN\s+KEY\s+REFERENCES', 'REFERENCES', constraints, flags=re.IGNORECASE)

        # Fix 2: Remove "NULLABLE" keyword (not valid SQL - NULL is the default)
        constraints = re.sub(r',?\s*NULLABLE\b', '', constraints, flags=re.IGNORECASE)

        # Fix 3: Remove "ON UPDATE CURRENT_TIMESTAMP" for PostgreSQL (MySQL only)
        if self.dialect == "postgresql":
            constraints = re.sub(r'\bON\s+UPDATE\s+CURRENT_TIMESTAMP\b', '', constraints, flags=re.IGNORECASE)

        # Fix 4: Clean up double spaces and trailing commas
        constraints = re.sub(r'\s+', ' ', constraints)
        constraints = re.sub(r',\s*$', '', constraints)
        constraints = re.sub(r',\s*,', ',', constraints)

        return constraints.strip()

    def _generate_field(self, field) -> str:
        """Generate SQL field definition."""
        # Handle both dict and string formats
        if isinstance(field, dict):
            name = field.get("name", "")
            field_type = field.get("type", "VARCHAR(255)")
            constraints_raw = field.get("constraints", "")
        else:
            # Field is just a string (column name)
            name = str(field)
            # Auto-detect type based on common column names
            if name == "id":
                field_type = "UUID"
                constraints_raw = "PRIMARY KEY DEFAULT gen_random_uuid()"
            elif "email" in name:
                field_type = "VARCHAR(255)"
                constraints_raw = "UNIQUE NOT NULL"
            elif "password" in name or "hash" in name:
                field_type = "VARCHAR(255)"
                constraints_raw = "NOT NULL"
            elif "created_at" in name or "updated_at" in name:
                field_type = "TIMESTAMP"
                constraints_raw = "DEFAULT NOW()"
            elif "_id" in name:
                field_type = "UUID"
                constraints_raw = ""
            else:
                field_type = "VARCHAR(255)"
                constraints_raw = ""

        # Handle constraints as string (new format) or list (old format)
        if isinstance(constraints_raw, str):
            # If constraints is already a SQL string, use it directly
            constraints = constraints_raw
        elif isinstance(constraints_raw, list):
            # Old format: list of constraint types
            constraints = constraints_raw
        else:
            constraints = []

        # Map generic types to SQL types
        sql_type = self._map_type(field_type)

        # Build field definition
        parts = [name, sql_type]

        # Handle constraints - if it's a string, use it directly; if list, parse it
        if isinstance(constraints, str) and constraints.strip():
            # Sanitize constraints string for valid SQL syntax
            constraints = self._sanitize_constraints(constraints)

            # New format: constraints is already a SQL string (e.g., "PRIMARY KEY DEFAULT gen_random_uuid()")
            # Replace the type if it's a primary key with default
            if "PRIMARY KEY" in constraints.upper():
                # Check if we need to override the type for UUID primary keys
                if "gen_random_uuid" in constraints.upper() and self.dialect == "postgresql":
                    parts[1] = "UUID"
                elif "UUID" in constraints.upper():
                    parts[1] = "UUID"
                elif "CHAR(36)" in constraints.upper() and self.dialect == "mysql":
                    parts[1] = "CHAR(36)"
            if constraints.strip():
                parts.append(constraints)
        elif isinstance(constraints, list):
            # Old format: list of constraint types (e.g., ["primary_key", "not_null"])
            if "primary_key" in constraints or field.get("primary_key"):
                if self.dialect == "postgresql":
                    if "id" in name:
                        parts[1] = "UUID PRIMARY KEY DEFAULT gen_random_uuid()"
                elif self.dialect == "mysql":
                    if "id" in name:
                        parts[1] = "CHAR(36) PRIMARY KEY DEFAULT (UUID())"
                elif self.dialect == "sqlite":
                    if "id" in name:
                        parts[1] = "TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16))))"
                else:
                    parts.append("PRIMARY KEY")

            if "unique" in constraints or field.get("unique"):
                parts.append("UNIQUE")

            if "not_null" in constraints or field.get("required"):
                parts.append("NOT NULL")

            if "nullable" in constraints or field.get("nullable"):
                pass  # NULL is default

        # Default values (only if not already in constraints string)
        if not isinstance(constraints, str) or "DEFAULT" not in constraints.upper():
            default = field.get("default")
            if default:
                if default == "now" or default == "current_timestamp":
                    if self.dialect == "postgresql":
                        parts.append("DEFAULT NOW()")
                    elif self.dialect == "mysql":
                        parts.append("DEFAULT CURRENT_TIMESTAMP")
                    elif self.dialect == "sqlite":
                        parts.append("DEFAULT (strftime('%s','now'))")
                else:
                    parts.append(f"DEFAULT {default}")

        # Foreign key (only if not already in constraints string)
        if not isinstance(constraints, str) or "REFERENCES" not in constraints.upper():
            references = field.get("references")
            if references:
                ref_table = references.get("table")
                ref_field = references.get("field", "id")
                on_delete = references.get("on_delete", "CASCADE")
                parts.append(f"REFERENCES {ref_table}({ref_field}) ON DELETE {on_delete}")

        return " ".join(parts)

    def _map_type(self, generic_type: str) -> str:
        """Map generic type to SQL dialect-specific type."""
        generic_type = generic_type.lower()

        type_map = {
            "postgresql": {
                "string": "VARCHAR(255)",
                "text": "TEXT",
                "int": "INTEGER",
                "integer": "INTEGER",
                "bigint": "BIGINT",
                "float": "REAL",
                "decimal": "DECIMAL",
                "boolean": "BOOLEAN",
                "bool": "BOOLEAN",
                "date": "DATE",
                "datetime": "TIMESTAMP",
                "timestamp": "TIMESTAMP",
                "json": "JSONB",
                "uuid": "UUID",
                "email": "VARCHAR(255)",
                "url": "TEXT",
            },
            "mysql": {
                "string": "VARCHAR(255)",
                "text": "TEXT",
                "int": "INT",
                "integer": "INT",
                "bigint": "BIGINT",
                "float": "FLOAT",
                "decimal": "DECIMAL",
                "boolean": "TINYINT(1)",
                "bool": "TINYINT(1)",
                "date": "DATE",
                "datetime": "DATETIME",
                "timestamp": "TIMESTAMP",
                "json": "JSON",
                "uuid": "CHAR(36)",
                "email": "VARCHAR(255)",
                "url": "TEXT",
            },
            "sqlite": {
                "string": "TEXT",
                "text": "TEXT",
                "int": "INTEGER",
                "integer": "INTEGER",
                "bigint": "INTEGER",
                "float": "REAL",
                "decimal": "REAL",
                "boolean": "INTEGER",
                "bool": "INTEGER",
                "date": "TEXT",
                "datetime": "INTEGER",
                "timestamp": "INTEGER",
                "json": "TEXT",
                "uuid": "TEXT",
                "email": "TEXT",
                "url": "TEXT",
            }
        }

        dialect_map = type_map.get(self.dialect, type_map["postgresql"])
        return dialect_map.get(generic_type, "TEXT")

    def _generate_index(self, table_name: str, index) -> str:
        """Generate index SQL. Handles both string and dict formats."""
        # Handle both string and dict formats
        if isinstance(index, str):
            # Check if LLM generated a full SQL statement instead of just field name
            if "CREATE INDEX" in index.upper() or "CREATE UNIQUE INDEX" in index.upper():
                # Parse the full SQL statement to extract index name and fields
                # Pattern: CREATE [UNIQUE] INDEX index_name ON table_name(fields)
                pattern = r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+ON\s+\w+\s*\(([^)]+)\)'
                match = re.search(pattern, index, re.IGNORECASE)
                if match:
                    idx_name = match.group(1)
                    fields_str = match.group(2).strip()
                    # Extract fields (handle comma-separated)
                    fields = [f.strip() for f in fields_str.split(',')]
                    unique = "UNIQUE" in index.upper()
                else:
                    # Fallback: try to extract just the field name from the statement
                    # Pattern: ON table_name(field_name)
                    fallback_pattern = r'ON\s+\w+\s*\(([^)]+)\)'
                    fallback_match = re.search(fallback_pattern, index, re.IGNORECASE)
                    if fallback_match:
                        fields_str = fallback_match.group(1).strip()
                        fields = [f.strip() for f in fields_str.split(',')]
                        idx_name = f"idx_{table_name}_{'_'.join(fields)}"
                        unique = "UNIQUE" in index.upper()
                    else:
                        # Last resort: use the string as field name
                        idx_name = f"idx_{table_name}_{index}"
                        fields = [index]
                        unique = False
            else:
            # Simple string format: just the field name
            idx_name = f"idx_{table_name}_{index}"
            fields = [index]
            unique = False
        else:
            # Dict format with full details
            idx_name = index.get("name", "")
            fields = index.get("fields", [])
            unique = index.get("unique", False)

            if not idx_name and fields:
                idx_name = f"idx_{table_name}_{'_'.join(fields)}"

        unique_str = "UNIQUE " if unique else ""
        fields_str = ", ".join(fields)

        return f"CREATE {unique_str}INDEX IF NOT EXISTS {idx_name} ON {table_name}({fields_str});"


class NoSQLSchemaGenerator:
    """Generate NoSQL schema for MongoDB, Firebase, etc."""

    def __init__(self, db_name: str, project_dir: str):
        self.db_name = db_name
        self.project_dir = project_dir

    def generate_schema(self, schema: Dict) -> Tuple[Any, List[str]]:
        """Generate NoSQL schema."""

        if "mongo" in self.db_name:
            return self._generate_mongodb_schema(schema)
        elif "firebase" in self.db_name or "firestore" in self.db_name:
            return self._generate_firestore_schema(schema)
        else:
            return {}, []

    def _generate_mongodb_schema(self, schema: Dict) -> Tuple[Dict, List[str]]:
        """Generate MongoDB schema with validation."""

        tables = schema.get("tables", [])
        collections = []
        mongo_schema = {"collections": []}

        for table in tables:
            collection_name = table.get("name", "")
            collections.append(collection_name)
            fields = table.get("fields", [])
            indexes = table.get("indexes", [])

            # Build validation schema
            required_fields = [f["name"] for f in fields if f.get("required") or f.get("constraints") and "not_null" in f["constraints"]]

            properties = {}
            for field in fields:
                field_name = field.get("name", "")
                field_type = field.get("type", "string")
                bson_type = self._map_to_bson_type(field_type)
                properties[field_name] = {"bsonType": bson_type}

            collection_def = {
                "name": collection_name,
                "indexes": self._convert_indexes(indexes),
                "validation": {
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": required_fields,
                        "properties": properties
                    }
                }
            }

            mongo_schema["collections"].append(collection_def)

        return mongo_schema, collections

    def _generate_firestore_schema(self, schema: Dict) -> Tuple[str, List[str]]:
        """Generate Firestore security rules."""

        tables = schema.get("tables", [])
        collections = [t.get("name", "") for t in tables]

        rules = """rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
"""

        for table in tables:
            coll_name = table.get("name", "")

            rules += f"""
    match /{coll_name}/{{docId}} {{
      allow read: if true;
      allow create: if request.auth != null;
      allow update, delete: if request.auth != null;
    }}
"""

        rules += """  }
}
"""

        return rules, collections

    def generate_indexes(self, schema: Dict) -> Dict:
        """Generate Firestore indexes configuration."""

        tables = schema.get("tables", [])
        indexes_config = {"indexes": []}

        for table in tables:
            coll_name = table.get("name", "")
            indexes = table.get("indexes", [])

            for idx in indexes:
                fields = idx.get("fields", [])

                index_def = {
                    "collectionGroup": coll_name,
                    "queryScope": "COLLECTION",
                    "fields": []
                }

                for field in fields:
                    index_def["fields"].append({
                        "fieldPath": field,
                        "order": "ASCENDING"
                    })

                indexes_config["indexes"].append(index_def)

        return indexes_config

    def _map_to_bson_type(self, generic_type: str) -> str:
        """Map generic type to BSON type."""
        type_map = {
            "string": "string",
            "text": "string",
            "int": "int",
            "integer": "int",
            "bigint": "long",
            "float": "double",
            "decimal": "decimal",
            "boolean": "bool",
            "bool": "bool",
            "date": "date",
            "datetime": "date",
            "timestamp": "date",
            "json": "object",
            "uuid": "string",
            "email": "string",
            "url": "string",
        }
        return type_map.get(generic_type.lower(), "string")

    def _convert_indexes(self, indexes: List[Dict]) -> List[Dict]:
        """Convert generic indexes to MongoDB format."""
        mongo_indexes = []

        for idx in indexes:
            fields = idx.get("fields", [])
            unique = idx.get("unique", False)

            key = {}
            for field in fields:
                key[field] = 1  # Ascending

            mongo_idx = {"key": key}
            if unique:
                mongo_idx["unique"] = True

            name = idx.get("name")
            if name:
                mongo_idx["name"] = name

            mongo_indexes.append(mongo_idx)

        return mongo_indexes
