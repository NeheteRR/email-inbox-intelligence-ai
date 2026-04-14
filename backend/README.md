# AI-Powered Email Intelligence System — Backend

A production-grade FastAPI backend that fetches Gmail emails, processes them through a **CrewAI multi-agent pipeline**, uses **Ollama (local LLM)** for summarization and classification, and persists results in **SQLite**.

---

## Architecture Overview

```
Gmail API
    │
    ▼
GmailService          ← Fetches & cleans raw emails (OAuth)
    │
    ▼
CrewAI Pipeline
  ├── Agent 1: Email Reader   ← Normalizes raw email text
  ├── Agent 2: Analyzer       ← Ollama LLM → summary / category / priority
  └── Agent 3: Structurer     ← Produces validated JSON record
    │
    ▼
SQLite Database       ← Persists structured results
    │
    ▼
FastAPI Endpoints     ← /process-emails  /emails
```

---

## Folder Structure

```
backend/
├── main.py                    # FastAPI app, lifespan, endpoints
├── gmail_service.py           # Gmail OAuth + email fetching
├── config.py                  # All settings via env vars
├── requirements.txt
├── .env.example
├── agents/
│   ├── __init__.py
│   ├── crew.py                # CrewAI orchestrator (sequential pipeline)
│   ├── email_reader.py        # Agent 1: clean email text
│   ├── analyzer.py            # Agent 2: Ollama LLM analysis
│   └── structurer.py          # Agent 3: produce final structured dict
└── services/
    ├── __init__.py
    ├── ollama_service.py      # Reusable Ollama REST API client
    └── database.py            # SQLite init / insert / query
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | f-string type hints require 3.10+ |
| Ollama | Latest | https://ollama.com |
| Google Cloud Project | — | Gmail API must be enabled |

---

## Step-by-Step Setup

### 1. Clone / Navigate to the backend directory

```bash
cd backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your preferred editor
```

### 5. Set up Gmail API credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Gmail API**
3. Go to **APIs & Services → Credentials**
4. Create **OAuth 2.0 Client ID** (Desktop App)
5. Download `credentials.json` → place it in the `backend/` directory
6. On first run, a browser window opens for Google login → `token.json` is saved automatically

### 6. Install and start Ollama

```bash
# Install Ollama (Linux/macOS)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull mistral

# Start Ollama server (keep running in a separate terminal)
ollama serve
```

> To use llama2 instead: set `OLLAMA_MODEL=llama2` in `.env` and run `ollama pull llama2`

### 7. Start the FastAPI backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Server is live at: **http://localhost:8000**

Interactive API docs: **http://localhost:8000/docs**

---

## API Endpoints

### `GET /` — Health Check

```bash
curl http://localhost:8000/
```

```json
{
  "status": "running",
  "service": "AI Email Intelligence System",
  "version": "1.0.0"
}
```

---

### `GET /process-emails` — Fetch, Analyze & Store Emails

Fetches Gmail emails → runs them through the CrewAI pipeline → stores in SQLite.

```bash
curl http://localhost:8000/process-emails
```

```json
{
  "message": "Email processing complete.",
  "processed": 8,
  "total_fetched": 10
}
```

---

### `GET /emails` — Retrieve All Processed Emails

Returns all stored emails from the database.

```bash
curl http://localhost:8000/emails
```

```json
{
  "total": 8,
  "emails": [
    {
      "id": 1,
      "sender": "boss@company.com",
      "subject": "Q3 Review Meeting",
      "summary": "Invitation to attend Q3 performance review on Friday at 3pm.",
      "category": "Meeting",
      "priority": "High",
      "created_at": "2026-04-13 10:22:01"
    }
  ]
}
```

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `GMAIL_CREDENTIALS_PATH` | `credentials.json` | OAuth credentials file |
| `GMAIL_TOKEN_PATH` | `token.json` | Saved OAuth token |
| `EMAIL_FETCH_LIMIT` | `10` | Max emails per fetch |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `mistral` | LLM model name |
| `OLLAMA_TIMEOUT` | `120` | Request timeout (seconds) |
| `DATABASE_PATH` | `emails.db` | SQLite database file path |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `credentials.json not found` | Missing OAuth file | Download from Google Cloud Console |
| `Cannot connect to Ollama` | Ollama not running | Run `ollama serve` |
| `model not found` | Model not pulled | Run `ollama pull mistral` |
| `Gmail API error` | Token expired / scope issue | Delete `token.json` and re-authenticate |
| `No emails found` | Empty inbox / wrong label | Check Gmail and `EMAIL_FETCH_LIMIT` |

---

## Frontend Integration

The backend is frontend-agnostic. Any frontend can consume:
- `GET /process-emails` to trigger the pipeline
- `GET /emails` to retrieve results as JSON

---

## Security Notes for Production

- Set `allow_origins` in CORS to your frontend domain (not `*`)
- Store `credentials.json` and `token.json` securely (not in version control)
- Add authentication middleware (OAuth2/JWT) to protect endpoints
- Use PostgreSQL instead of SQLite for production workloads
