# 6-Agent System - Implementation Plan

## Overview

Split the monolithic 2030-line system prompt into 6 focused agents, each handling specific phases.

## Agent Structure

### 1. Idea Agent (Phases 1-3)
**File:** `idea_agent.py`  
**System Prompt Size:** ~400 lines (vs 2030)

**Phases:**
- **Phase 1:** Project Discovery
- **Phase 2:** External Tools & APIs
- **Phase 3:** Tech Stack Selection

**What to Include:**
- Deep discovery framework (extract before asking)
- Smart question generation
- External service detection logic
- Tech stack research and selection
- Storage-first approach for each phase
- Phase completion checks

**Functions Needed:**
- `handle_phase_1()` - Project discovery
- `handle_phase_2()` - External tools
- `handle_phase_3()` - Tech stack
- `_extract_project_info()` - Parse user messages
- `_check_storage()` - Load existing data
- `_generate_smart_question()` - Context-aware questions

**System Prompt Sections:**
- Phase 1 rules (deep discovery, complete info)
- Phase 2 rules (external tools only)
- Phase 3 rules (tech stack selection with research)
- Intelligent extraction framework
- Storage-first mandatory rules

---

### 2. Design Agent (Phases 4-6)
**File:** `design_agent.py`  
**System Prompt Size:** ~500 lines

**Phases:**
- **Phase 4:** Database Design
- **Phase 5:** Backend Design
- **Phase 6:** Frontend Design

**What to Include:**
- Complete schema requirements (columns, types, constraints)
- Backend endpoint design
- Business logic clarification
- Frontend page/component design
- Design approval workflow
- Must complete before Phase 7

**Functions Needed:**
- `handle_phase_4()` - Database schema design
- `handle_phase_5()` - Backend architecture
- `handle_phase_6()` - Frontend architecture
- `_validate_schema_complete()` - Check schema has all columns/types
- `_design_endpoints()` - Generate API endpoints
- `_design_pages()` - Generate frontend pages

**System Prompt Sections:**
- Phase 4 rules (complete schema with columns/types)
- Phase 5 rules (all endpoints, business logic)
- Phase 6 rules (all pages, components)
- Design completion verification
- Approval workflow

---

### 3. Setup Agent (Phase 7)
**File:** `setup_agent.py`  
**System Prompt Size:** ~300 lines

**Phases:**
- **Phase 7:** Create All Project Files

**What to Include:**
- File generation logic
- Starter code creation
- Backend file structure
- Frontend file structure
- Verification (backend ↔ frontend match)
- Only runs after Phase 5 & 6 approved

**Functions Needed:**
- `handle_phase_7()` - File creation
- `_verify_prerequisites()` - Check Phase 5 & 6 complete
- `_create_backend_files()` - Generate backend structure
- `_create_frontend_files()` - Generate frontend structure
- `_verify_integration()` - Check API endpoints match

**System Prompt Sections:**
- Phase 7 rules (file creation only)
- Prerequisites check (Phase 5 & 6)
- File generation process
- Verification steps

---

### 4. Planning Agent (Phases 8-9)
**File:** `planning_agent.py`  
**System Prompt Size:** ~350 lines

**Phases:**
- **Phase 8:** Documentation
- **Phase 9:** Final Touches & Delivery

**What to Include:**
- Documentation generation (README, plan.md, task.md)
- Roadmap creation
- AI tool instructions (if needed)
- Team workflow (if needed)
- Final verification
- Project completion summary

**Functions Needed:**
- `handle_phase_8()` - Documentation generation
- `handle_phase_9()` - Final touches
- `_generate_docs()` - Create all documentation
- `_generate_roadmap()` - Create project timeline
- `_create_ai_instructions()` - AI tool specific files
- `_final_verification()` - Check everything complete

**System Prompt Sections:**
- Phase 8 rules (documentation)
- Phase 9 rules (final touches)
- Documentation templates
- Completion checklist

---

### 5. Git Agent (Version Control)
**File:** `git_agent.py`  
**System Prompt Size:** ~200 lines

**Phases:**
- **Throughout:** Git operations
- **Phase 9:** Final Git setup

**What to Include:**
- Repository initialization
- Smart commit messages
- Phase completion commits
- Branch strategy (if needed)
- Tag management

**Functions Needed:**
- `initialize_repo()` - Git init
- `create_commit()` - Create commits
- `create_tag()` - Version tags
- `_generate_commit_message()` - Smart commit messages
- `_check_git_status()` - Git status

**System Prompt Sections:**
- Git workflow rules
- Commit message format
- Branch strategy
- Tag conventions

---

### 6. Live Agent (Phase 10)
**File:** `live_agent.py`  
**System Prompt Size:** ~300 lines

**Phases:**
- **Phase 10:** Live Development Mode

**What to Include:**
- File watching
- Browser console tracking
- Proactive code improvements
- Error detection
- Auto-fix suggestions
- Improvement logging

**Functions Needed:**
- `activate()` - Start live mode
- `deactivate()` - Stop live mode
- `get_status()` - Current status
- Uses `LiveModeController` from `live_mode/`

**System Prompt Sections:**
- Phase 10 activation rules
- Monitoring guidelines
- When to help vs stay quiet
- Improvement logging
- User commands (status, help, etc.)

---

## Agent Router

**New File:** `agent_router.py`

**Purpose:** Route requests to correct agent based on current phase.

```python
class AgentRouter:
    def __init__(self, ...):
        self.idea_agent = IdeaAgent(...)
        self.design_agent = DesignAgent(...)
        self.setup_agent = SetupAgent(...)
        self.planning_agent = PlanningAgent(...)
        self.git_agent = GitAgent(...)
        self.live_agent = LiveAgent(...)
    
    def route(self, phase: int, user_message: str):
        if phase in [1, 2, 3]:
            return self.idea_agent
        elif phase in [4, 5, 6]:
            return self.design_agent
        elif phase == 7:
            return self.setup_agent
        elif phase in [8, 9]:
            return self.planning_agent
        elif phase == 10:
            return self.live_agent
```

---

## System Prompt Extraction Plan

### From Current `system_prompt.py` (2030 lines):

**Extract to Idea Agent (~400 lines):**
- Lines 139-273: Phase 1 (Project Discovery)
- Lines 275-363: Phase 2 (External Tools)
- Lines 372-500: Phase 3 (Tech Stack)
- Lines 15-115: Intelligent Extraction Framework
- Lines 35-40: Storage-first rules

**Extract to Design Agent (~500 lines):**
- Lines 502-694: Phase 4 (Database Design)
- Lines 695-917: Phase 5 (Backend Design)
- Lines 925-1169: Phase 6 (Frontend Design)
- Lines 1965-1993: Phase completion checklists

**Extract to Setup Agent (~300 lines):**
- Lines 1184-1295: Phase 7 (File Creation)
- Lines 1989-1993: Prerequisites check

**Extract to Planning Agent (~350 lines):**
- Lines 1296-1349: Phase 8 (Documentation)
- Lines 1350-1440: Phase 9 (Final Touches)

**Extract to Git Agent (~200 lines):**
- Lines 2117-2169: Git Integration section
- Add Git-specific rules

**Extract to Live Agent (~300 lines):**
- Lines 1441-1901: Phase 10 (Live Development Mode)
- Lines 1956-1963: Live Development functions

**Shared Rules (Keep in Router or Core):**
- Lines 15-81: Critical Rules (1-12)
- Lines 82-90: User Profile
- Lines 2000-2011: Critical Reminders

---

## Implementation Steps

### Step 1: ✅ Create Agent Skeletons (DONE)
- [x] Create 6 agent files with basic structure
- [x] Create `__init__.py` for agents package
- [x] Create planning document

### Step 2: Extract System Prompts
- [ ] Extract Phase 1-3 prompts → Idea Agent
- [ ] Extract Phase 4-6 prompts → Design Agent
- [ ] Extract Phase 7 prompt → Setup Agent
- [ ] Extract Phase 8-9 prompts → Planning Agent
- [ ] Extract Git section → Git Agent
- [ ] Extract Phase 10 → Live Agent

### Step 3: Create Agent Router
- [ ] Create `agent_router.py`
- [ ] Implement phase-based routing
- [ ] Add agent initialization

### Step 4: Update Core Agent
- [ ] Modify `core.py` to use router
- [ ] Keep backward compatibility
- [ ] Test routing logic

### Step 5: Test Each Agent
- [ ] Test Idea Agent (Phases 1-3)
- [ ] Test Design Agent (Phases 4-6)
- [ ] Test Setup Agent (Phase 7)
- [ ] Test Planning Agent (Phases 8-9)
- [ ] Test Git Agent
- [ ] Test Live Agent (Phase 10)

### Step 6: Cleanup
- [ ] Remove old monolithic prompt (after testing)
- [ ] Update documentation
- [ ] Verify all phases work

---

## Benefits

1. **Smaller Prompts:** 200-500 lines each vs 2030 lines
2. **Faster Responses:** Less context = faster LLM calls
3. **Easier Updates:** Change one agent, not entire system
4. **Better Focus:** Each agent does one thing well
5. **Modular:** Add/remove agents independently
6. **Maintainable:** Clear separation of concerns

---

## Next Steps

1. Review this plan
2. Extract system prompts to each agent
3. Build agent router
4. Test each agent independently
5. Integrate with core system
6. Remove old monolithic prompt (after verification)

