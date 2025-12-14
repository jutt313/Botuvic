# BOTUVIC Interactive UI - Claude Code Style

Beautiful, interactive terminal UI for BOTUVIC with Claude Code-style interface.

## ✨ New Features

### Interactive Components
- **Permission Prompts** - Visual file/action approval dialogs
- **Multi-Select Menus** - Checkbox-style file/option selection
- **Real-time Status** - Spinners and progress indicators
- **Code Display** - Syntax-highlighted code with before/after diffs
- **Activity Panels** - Shows what BOTUVIC is doing in real-time
- **Rich Tables** - Beautiful data presentation
- **Markdown Rendering** - Formatted documentation display

### Controls
- **↑/↓ Arrow Keys** - Navigate options
- **Space** - Toggle checkboxes
- **Enter** - Confirm selection
- **Ctrl+C** - Cancel/Exit

## 🚀 Installation

### 1. Install Dependencies
```bash
cd /Users/chaffanjutt/Downloads/dev/Botuvic/cli
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Install/Update BOTUVIC
```bash
pip install -e .
```

This installs two commands:
- `botuvic` - New interactive UI (Claude Code style)
- `botuvic-simple` - Original simple text interface

## 🎯 Usage

### Run with Interactive UI
```bash
botuvic
```

### Run Demo (See All UI Features)
```bash
python -m botuvic.ui.demo
```

### Commands in Chat
- `help` - Show available commands
- `status` - Show project status and progress
- `clear` - Clear screen
- `exit` - Exit BOTUVIC (also: quit, q, bye)

## 📦 New Files Created

```
cli/botuvic/
├── ui/
│   ├── interactive.py       ✨ NEW - Interactive UI components
│   └── demo.py              ✨ NEW - UI feature demo
├── main_interactive.py      ✨ NEW - Enhanced CLI entry point
└── requirements.txt         📝 UPDATED - Added questionary, prompt-toolkit, pygments

setup.py                     📝 UPDATED - Added new entry points
```

## 🎨 UI Components Available

### 1. Status Messages
```python
ui.show_status("Processing...")
ui.show_success("Done!")
ui.show_error("Failed!")
ui.show_warning("Be careful")
ui.show_info("FYI")
```

### 2. User Input
```python
# Text input
name = ui.ask_text("Your name?")

# Select one
choice = ui.ask_select("Choose:", ["A", "B", "C"])

# Select multiple
choices = ui.ask_checkbox("Pick:", ["X", "Y", "Z"])

# Confirm
ok = ui.ask_confirm("Proceed?")
```

### 3. Permission Request
```python
files = ["app.py", "config.py"]
if ui.ask_permission("modify these files", files):
    # User approved
    pass
```

### 4. File Selection
```python
files = ["file1.py", "file2.py", "file3.py"]
selected = ui.select_files(files, "Choose files:")
```

### 5. Code Display
```python
# Show code
ui.show_code(code, language="python", title="app.py")

# Show before/after diff
ui.show_code_diff("app.py", old_code, new_code, "python")
```

### 6. Activity Indicators
```python
# Show what agent is doing
ui.show_activity_panel("searching", "Searching for solutions...")

# With spinner
result = ui.with_spinner("Loading", lambda: do_work())
```

### 7. Data Display
```python
# Table
ui.show_table("Files", ["Name", "Lines"], [["app.py", "234"]])

# Markdown
ui.show_markdown("# Title\n\nContent here")

# Project summary
ui.show_project_summary(project_data)

# Roadmap
ui.show_roadmap(roadmap_data)
```

## 🔄 How It Works

When you run `botuvic`:

1. **Banner** - Shows BOTUVIC logo and version
2. **Initialization** - Loads agent with status indicator
3. **Project Detection** - Shows if NEW or EXISTING project
4. **Context Display** - Shows project summary (if exists)
5. **Interactive Chat** - Beautiful prompt with real-time feedback
6. **Function Execution** - Shows activity panels for each action
7. **Permission Requests** - Asks before file modifications
8. **Results Display** - Syntax-highlighted code and formatted output

## 🎭 Example Session

```
╔═══════════════════════════════════════╗
║      BOTUVIC - AI Project Manager     ║
╚═══════════════════════════════════════╝

⚙️  Initializing BOTUVIC agent...
✅ Agent initialized
ℹ️  🆕 Mode: NEW PROJECT

💬 Chat with BOTUVIC

👤 You: Help me build a todo app

🤖 BOTUVIC is thinking...

┌─ 🤖 BOTUVIC ─────────────────────────┐
│                                      │
│ I'll help you build a todo app!     │
│ Let me ask a few questions first... │
│                                      │
└──────────────────────────────────────┘

? What's your coding experience level?
❯ Beginner
  Intermediate
  Advanced
```

## 🐛 Troubleshooting

### If you see import errors:
```bash
pip install --upgrade questionary prompt-toolkit pygments rich
```

### To test UI without full agent:
```bash
python -m botuvic.ui.demo
```

### To use old simple UI:
```bash
botuvic-simple
```

## 📝 Notes

- All functionality from original BOTUVIC is preserved
- Interactive UI adds visual feedback but doesn't change core behavior
- Progress is still saved to `.botuvic/` folder
- You can switch between `botuvic` and `botuvic-simple` anytime

## 🎉 Enjoy!

The new UI makes BOTUVIC feel like a modern AI assistant with:
- Clear visual feedback
- Interactive controls
- Beautiful code display
- Professional appearance

Try the demo to see all features:
```bash
python -m botuvic.ui.demo
```
