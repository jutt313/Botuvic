# BOTUVIC - AI Project Manager Agent

## Vision

BOTUVIC is an intelligent terminal-based AI agent that manages software projects from start to finish. It combines conversational AI, active code execution, project planning, and progress tracking into a single tool that helps developers stay organized and productive.

## Core Concept

Instead of juggling multiple tools (project management, code analysis, testing, git), developers interact with BOTUVIC through natural conversation. BOTUVIC plans the project, tracks progress, analyzes code, finds errors, executes commands, and verifies completion.

**Think:** AI project manager + code reviewer + terminal assistant in one.

## Key Features We're Building

### 1. **Conversational CLI Interface**
- Natural language chat in terminal
- User speaks in plain English
- AI understands commands and questions
- Built with Python + Click framework

### 2. **Multi-LLM Support**
- Claude (Anthropic)
- ChatGPT (OpenAI)
- Gemini (Google)
- Ollama (local, private)
- Adapter pattern for easy switching

### 3. **Intelligent Project Planning**
- User describes project idea
- AI generates complete roadmap
- Breaks down into phases and tasks
- Recommends tech stack
- Creates file structure
- Saves plan locally (`.botuvic/` folder)

### 4. **Active Agent Capabilities**
- **Code Scanner** - Reads and analyzes all project files
- **Error Detection** - Finds bugs, missing features, issues
- **Command Executor** - Runs tests, starts servers, installs packages
- **File Creator** - Generates code files and components
- **Auto-fix** - Suggests and applies code fixes

### 5. **Progress Tracking & Verification**
- Monitors task completion per phase
- Compares actual code vs. planned features
- Phase verification system (blocks progression if incomplete)
- Shows percentage complete
- Ensures quality before next phase

### 6. **Git Integration**
- Auto-commit on phase completion
- Smart commit messages (AI-generated)
- Branch management per phase
- PR description generation
- Git status tracking

### 7. **Report Generation**
- `PLAN.md` - Complete project roadmap
- `TODO.md` - All tasks with status
- `REPORT.md` - Progress and analytics
- `ERRORS.log` - Bug tracking
- All saved in `.botuvic/reports/`

### 8. **Web Dashboard**
- Visual project overview
- View all projects and progress
- Real-time sync with terminal
- Read reports online
- Manage settings and API keys
- Analytics and insights

### 9. **Authentication & User Management**
- User accounts (email/password, OAuth)
- Secure API key storage (encrypted)
- Multi-device support
- Session management

## Technical Stack

### CLI Tool (Python)
- **Language:** Python 3.8+
- **CLI Framework:** Click
- **Terminal UI:** Rich (beautiful output)
- **AI Integration:** Anthropic, OpenAI, Google APIs
- **Local Storage:** JSON files
- **Code Execution:** subprocess
- **Git Integration:** GitPython
- **File Operations:** os, pathlib, glob

### Web Dashboard
- **Frontend:** React / Next.js
- **Backend:** Node.js + Express
- **Database:** PostgreSQL
- **Auth:** JWT tokens
- **API:** RESTful endpoints
- **Sync:** Real-time updates

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   USER                          │
│  (Terminal + Web Dashboard)                     │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│              BOTUVIC CLI                        │
│  ┌──────────────────────────────────────────┐   │
│  │  Conversational Interface (Click)        │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │  Multi-LLM Adapter System                │   │
│  │  (Claude/ChatGPT/Gemini/Ollama)          │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │  Core Modules:                           │   │
│  │  - Project Planner                       │   │
│  │  - Code Scanner                          │   │
│  │  - Command Executor                      │   │
│  │  - Progress Tracker                      │   │
│  │  - Phase Verifier                        │   │
│  │  - Git Manager                           │   │
│  │  - Report Generator                      │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │  Local Storage (.botuvic/)               │   │
│  │  - project.json                          │   │
│  │  - phases.json                           │   │
│  │  - progress.json                         │   │
│  │  - errors.json                           │   │
│  │  - config.json                           │   │
│  └──────────────────────────────────────────┘   │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│           WEB DASHBOARD                         │
│  ┌──────────────────────────────────────────┐   │
│  │  Frontend (React)                        │   │
│  │  - Projects view                         │   │
│  │  - Progress tracking                     │   │
│  │  - Reports viewer                        │   │
│  │  - Settings                              │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │  Backend API (Node.js)                   │   │
│  │  - Auth endpoints                        │   │
│  │  - Project CRUD                          │   │
│  │  - Sync service                          │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │  PostgreSQL Database                     │   │
│  │  - users                                 │   │
│  │  - projects                              │   │
│  │  - api_keys (encrypted)                  │   │
│  │  - subscriptions                         │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## Data Storage Structure

### Local Files (.botuvic/)
```
project-root/
├── .botuvic/
│   ├── config.json          # User settings, API keys (encrypted)
│   ├── project.json         # Project metadata, description, tech stack
│   ├── phases.json          # Phase definitions, tasks, status
│   ├── progress.json        # Task completion tracking
│   ├── errors.json          # Found errors and issues
│   ├── history.json         # Chat and command history
│   └── reports/
│       ├── PLAN.md          # Project roadmap
│       ├── TODO.md          # Task list
│       ├── REPORT.md        # Progress report
│       └── ERRORS.log       # Error log
```

### Database Schema (PostgreSQL)

**users**
- id (UUID, primary key)
- email (unique)
- password_hash
- name
- created_at
- updated_at
- subscription_plan (free/pro/premium)
- stripe_customer_id

**projects**
- id (UUID, primary key)
- user_id (foreign key)
- name
- description
- tech_stack (JSON)
- current_phase
- progress_percentage
- status (active/paused/complete)
- project_data (JSON) - phases, tasks, errors
- created_at
- updated_at

**api_keys**
- id (UUID, primary key)
- user_id (foreign key)
- provider (claude/openai/gemini)
- api_key_encrypted
- created_at
- updated_at

**subscriptions**
- id (UUID, primary key)
- user_id (foreign key)
- plan (free/pro/premium)
- status (active/cancelled/expired)
- current_period_start
- current_period_end
- stripe_subscription_id

## Development Phases

### Phase 1: Core CLI Foundation (Week 1-2)
- CLI interface with Click
- Chat conversation system
- Command parsing
- Local storage setup (JSON files)
- Configuration management

### Phase 2: AI Integration (Week 2-3)
- Multi-LLM adapter system
- Claude API integration
- OpenAI API integration
- Gemini API integration
- Ollama local integration
- API key management (encrypted)
- Context builder for prompts

### Phase 3: Project Management (Week 3-4)
- `init` command - project initialization
- AI-powered project planner
- Phase and task generation
- Progress tracking system
- Phase verification logic

### Phase 4: Active Agent Features (Week 4-6)
- Code scanner (file reading + analysis)
- Error detection system
- Error deduplication
- Command executor (subprocess)
- File creator (AI code generation)
- Auto-fix suggestions and application

### Phase 5: Git Integration (Week 6-7)
- Git wrapper (GitPython)
- Auto-commit on phase completion
- Smart commit message generation
- Branch management
- PR description generation

### Phase 6: Reports & Status (Week 7-8)
- Report generator
- PLAN.md generation
- TODO.md generation
- REPORT.md generation
- ERRORS.log generation
- Status command with progress visualization

### Phase 7: Web Dashboard (Week 8-11)
- Backend API setup (Node.js + Express)
- PostgreSQL database setup
- User authentication (JWT)
- Frontend setup (React/Next.js)
- Projects list view
- Project detail view
- Reports viewer
- Settings page
- Real-time sync service

### Phase 8: Polish & Testing (Week 11-12)
- Error handling improvements
- User experience refinements
- Documentation
- Unit tests
- Integration tests
- Bug fixes

## Key Workflows

### Workflow 1: Starting a New Project
1. User runs `botuvic init`
2. AI asks clarifying questions
3. Generates complete project plan with phases
4. Creates `.botuvic/` folder structure
5. Saves plan locally
6. User can view plan in terminal or dashboard

### Workflow 2: Code Scanning
1. User runs `botuvic scan`
2. BOTUVIC reads all code files
3. Sends to AI with project context
4. AI analyzes code vs. plan
5. Detects errors, missing features, issues
6. Deduplicates errors
7. Generates ERRORS.log report

### Workflow 3: Phase Completion & Verification
1. User works on Phase 1 tasks
2. User runs `botuvic phase-done`
3. BOTUVIC loads phase requirements
4. Scans all code
5. Verifies tasks completed
6. Checks code quality
7. Either approves (auto-commit) or blocks with feedback

### Workflow 4: Command Execution
1. User runs `botuvic run "npm test"`
2. BOTUVIC executes command via subprocess
3. Captures stdout/stderr
4. AI analyzes output
5. Reports results to user
6. Suggests fixes if tests fail

### Workflow 5: Natural Conversation
1. User: `botuvic "create a login component"`
2. BOTUVIC checks project plan and tech stack
3. Generates appropriate code for the stack
4. Creates file in correct directory
5. Updates progress tracker
6. Reports back to user

## Success Criteria

- ✅ Natural conversation works smoothly
- ✅ Multi-LLM switching works seamlessly
- ✅ Project plans are accurate and useful
- ✅ Code scanning detects real issues
- ✅ Phase verification prevents incomplete work
- ✅ Git integration saves time
- ✅ Dashboard syncs in real-time
- ✅ Local-first architecture respects privacy
- ✅ Fast response times (<2s for most operations)
- ✅ User satisfaction: saves time and reduces cognitive load

## Privacy & Security

- **Local-first:** All data stored locally first
- **Encrypted keys:** API keys encrypted at rest
- **Optional sync:** Cloud sync is opt-in
- **No tracking:** No analytics or tracking
- **User control:** User owns all data
- **Secure auth:** JWT tokens, password hashing
- **HTTPS only:** All network communication encrypted

## Target Users

1. **Solo developers** - Need project organization
2. **Freelancers** - Managing multiple client projects
3. **Students** - Learning project structure
4. **Small teams** - Coordinating without heavy tools
5. **Open source maintainers** - Tracking contributions

## Future Enhancements (Post-MVP)

- CI/CD integration
- IDE plugins (VS Code, JetBrains)
- Team collaboration features
- Mobile dashboard app
- Voice commands
- Custom agent builder
- Performance monitoring
- Auto-documentation generation

---

**BOTUVIC: Your AI project manager that actually works.**

*Start date: [Current Date]*  
*Target MVP: 12 weeks*  
*Tech: Python + Click + PostgreSQL + React + AI*
