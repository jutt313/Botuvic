# BOTUVIC Backend

FastAPI backend for BOTUVIC project manager.

## Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your Supabase credentials (or copy from root `.env`)

4. Run the server:
```bash
python3 main.py
# Or
uvicorn main:app --reload
```

Server will run on http://localhost:8000

