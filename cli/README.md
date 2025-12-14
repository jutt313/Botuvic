# BOTUVIC CLI

AI-powered project management from the terminal.

## Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install:
```bash
pip install -r requirements.txt
pip install -e .
```

3. Run:
```bash
botuvic
```

## Structure

```
cli/
├── botuvic/
│   ├── agent/          # Agent system (to be built)
│   ├── config.py       # Config management (to be built)
│   └── main.py         # Entry point
├── requirements.txt
└── setup.py
```

