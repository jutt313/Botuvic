# BOTUVIC MCP Server Setup

## For Users

### 1. Get API Key
Visit https://botuvic.com and sign up to get your API key.

### 2. Install BOTUVIC
```bash
pip install botuvic
```

### 3. Configure Cursor

Add to Cursor settings (`~/.cursor/mcp_settings.json` or via UI):

```json
{
  "mcpServers": {
    "botuvic": {
      "command": "python",
      "args": ["-m", "botuvic.mcp_server"],
      "env": {
        "BOTUVIC_API_KEY": "sk_live_YOUR_KEY_HERE",
        "BOTUVIC_API_URL": "https://botuvic-api.onrender.com",
        "DEEPSEEK_API_KEY": "your_deepseek_key",
        "BOTUVIC_PROJECT_DIR": "/path/to/your/project"
      }
    }
  }
}
```

### 4. Use in Cursor

Open Cursor and type:
- "Create a SaaS app for task management"
- "Activate live mode"
- "Generate tests"
- "Check if ready to deploy"

---

## For Developers (Deploy API)

### 1. Fork & Clone
```bash
git clone https://github.com/yourusername/Botuvic.git
cd Botuvic
```

### 2. Deploy to Render

Click: [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

Or manually:
1. Create account on render.com
2. New → Blueprint
3. Connect GitHub repo
4. render.yaml will auto-configure

### 3. Get API URL
After deploy, copy your API URL:
```
https://botuvic-api-xxxx.onrender.com
```

### 4. Create First API Key

```bash
curl -X POST https://your-api.onrender.com/keys/create \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

Response:
```json
{
  "key": "sk_live_abc123...",
  "user_id": 1,
  "email": "user@example.com"
}
```

### 5. Test Validation

```bash
curl -X POST https://your-api.onrender.com/validate \
  -H "Content-Type: application/json" \
  -d '{"key": "sk_live_abc123..."}'
```

---

## Local Development

### Run API Server
```bash
cd api
pip install -r requirements.txt
python main.py
```

API runs on http://localhost:8000

### Test MCP Server
```bash
export BOTUVIC_API_KEY="sk_live_test"
export BOTUVIC_API_URL="http://localhost:8000"
export DEEPSEEK_API_KEY="your_key"

python -m botuvic.mcp_server
```

---

## Troubleshooting

**"Invalid API key"**
- Check BOTUVIC_API_KEY is set correctly
- Verify key is active: `curl https://your-api.onrender.com/validate -d '{"key": "..."}'`

**"DEEPSEEK_API_KEY not set"**
- BOTUVIC uses DeepSeek for LLM
- Get key at https://platform.deepseek.com

**MCP not showing in Cursor**
- Restart Cursor after adding config
- Check logs: Cursor → Help → Show Logs → MCP

**Database errors**
- Render free tier sleeps after inactivity
- First request may be slow (wakes up database)
