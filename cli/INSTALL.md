# BOTUVIC CLI Installation Guide

## Quick Start

1. **Navigate to CLI directory:**
   ```bash
   cd cli
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Install/Reinstall the package:**
   ```bash
   pip install -e .
   ```

4. **Run BOTUVIC:**
   ```bash
   botuvic
   ```

## If Command Not Found

If you get `command not found: botuvic`:

1. **Make sure virtual environment is activated:**
   ```bash
   source venv/bin/activate
   ```

2. **Reinstall the package:**
   ```bash
   pip install -e .
   ```

3. **Verify installation:**
   ```bash
   which botuvic
   # Should show: /path/to/cli/venv/bin/botuvic
   ```

4. **Try running again:**
   ```bash
   botuvic
   ```

## Alternative: Use Python Module

If the command still doesn't work, you can run directly:

```bash
python -m botuvic.main_interactive
```

## Troubleshooting

### Virtual Environment Not Activated
- Make sure you see `(venv)` in your terminal prompt
- If not, run: `source venv/bin/activate`

### Package Not Installed
- Run: `pip install -e .` from the `cli/` directory
- This installs the package in "editable" mode

### Missing Dependencies
- Run: `pip install -r requirements.txt`
- Then: `pip install -e .`

### Permission Issues
- Make sure you have write access to the `venv/` directory
- Try: `chmod -R u+w venv/`

## Environment Variables

Make sure you have a `.env` file in the project root with:

```bash
OPENAI_API_KEY=your-key-here
TAVILY_API_KEY=your-key-here  # Optional, for web search
```

The CLI will auto-configure with OpenAI if `OPENAI_API_KEY` is found.

