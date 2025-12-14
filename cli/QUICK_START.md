# Quick Start - BOTUVIC CLI

## You're Already in the CLI Directory! ✅

Since you're already in the `cli` directory, just run these commands:

### Option 1: Manual Steps

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install/update the package
python3 -m pip install -e .

# 3. Run BOTUVIC
botuvic
```

### Option 2: Use the Runner Script

```bash
./run.sh
```

### Option 3: Direct Python Execution

If the command still doesn't work:

```bash
source venv/bin/activate
python3 -m botuvic.main_interactive
```

## Troubleshooting

### If `source venv/bin/activate` doesn't work:

Try:
```bash
. venv/bin/activate
```

Or use full path:
```bash
source /Users/chaffanjutt/Downloads/dev/Botuvic/cli/venv/bin/activate
```

### If `pip` command not found:

Use:
```bash
python3 -m pip install -e .
```

### Verify venv is activated:

You should see `(venv)` in your prompt:
```bash
(venv) chaffanjutt@Affans-MacBook-Air cli %
```

## What You Should See

After running `botuvic`, you should see:

```
╭─────────────────────────────────────────────────────────────────╮
│     ██████╗  ██████╗ ████████╗██╗   ██╗██╗   ██╗██╗ ██████╗     │
│     ██╔══██╗██╔═══██╗╚══██╔══╝██║   ██║██║   ██║██║██╔════╝     │
│     ██████╔╝██║   ██║   ██║   ██║   ██║██║   ██║██║██║          │
│     ██╔══██╗██║   ██║   ██║   ██║   ██║╚██╗ ██╔╝██║██║          │
│     ██████╔╝╚██████╔╝   ██║   ╚██████╔╝ ╚████╔╝ ██║╚██████╗     │
│     ╚═════╝  ╚═════╝    ╚═╝    ╚═════╝   ╚═══╝  ╚═╝ ╚═════╝     │
│                                                                 │
│        Your AI Project Manager from Idea to Deployment         │
│                                                                 │
│   Build anything with AI guidance. BOTUVIC plans, tracks,    │
│   codes, debugs, and deploys your project from start to        │
│   finish. Whether you're a beginner or expert, BOTUVIC         │
│   adapts to your skill level and keeps you on track.           │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯

Type your message or press / for commands

You: _
```

