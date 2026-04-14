# AI-Powered Email Intelligence System

A full-stack, agentic AI application that fetches Gmail emails, orchestrates them through a **CrewAI multi-agent pipeline** powered by **Google Gemini 2.5 Flash**, and surfaces actionable insights to a beautiful **React / Next.js** dashboard.

---

## 🌟 Key Features

*   **Agentic AI Pipeline**: Utilizes CrewAI with three distinct agents (Email Reader, Analyzer, Structurer) to intelligently parse, categorize, and prioritize incoming emails.
*   **Intent-Based Classification**: Automatically categorizes emails into actionable buckets like *Meetings, Events, Tasks, Follow-ups, Reports, References, Finance, Promotions,* and *Other*.
*   **Actionable Dashboard (Next.js)**: Read summaries, generate LLM reply drafts, send emails, forward threads, and organize your inbox directly from the dashboard.
*   **Google Calendar Integration**: Automatically extract meeting details from email threads and generate Google Calendar events with AI.
*   **Robust Backend**: Built on **FastAPI** leveraging **PostgreSQL** for reliable data persistence and rapid querying.
*   **Secure & Flexible**: Configured entirely via environment variables, integrating securely via standard Google API OAuth 2.0.

---

## 🏗️ Architecture Overview

The project is structured as a monorepo with distinct `frontend` and `backend` services.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│                 │       │                 │       │                 │
│  Gmail Inbox    ├──────►│  FastAPI Server │◄──────┤ Next.js UI      │
│                 │       │                 │       │                 │
└─┬─────────────┬─┘       └─┬─────────────┬─┘       └─────────────────┘
  │             │           │             │
  │   OAuth     │           │   CrewAI    │
  ▼             ▼           ▼             ▼
┌────────┐ ┌────────┐   ┌────────┐   ┌───────────┐
│ Send   │ │ Modify │   │ Reader │   │ PostgreSQL│
│ Reply  │ │ Labels │   ├────────┤   └───────────┘
│ Forward│ │ Events │   │Analyzer│        ▲
└────────┘ └────────┘   ├────────┤        │
                        │ Struct.├────────┘
                        └────────┘
                             │
                        ┌────▼────┐
                        │ Gemini  │
                        │ 2.5 SDK │
                        └─────────┘
```

---

## 📂 Project Structure

```
ai-email-intelligence-system/
├── backend/                  # FastAPI Application
│   ├── agents/               # CrewAI Orchestration (reader, analyzer, structurer)
│   ├── services/             # Gemini API, Calendar, Database logic
│   ├── config.py             # Environment configurations
│   ├── gmail_service.py      # Core Gmail OAuth API integrations
│   ├── main.py               # REST API Endpoints
│   └── requirements.txt      # Python dependencies
├── frontend/                 # Next.js UI
│   ├── src/                  # React Components & Dashboard Layouts
│   ├── public/               # Static assets
│   └── package.json          # Node dependencies
└── .env                      # Global environment variables
```

---

## 🚀 Getting Started

### Prerequisites
*   **Python 3.11+**
*   **Node.js 18+** / npm
*   **PostgreSQL** Database
*   **Google Cloud Project** with Gmail API & Google Calendar API Enabled
*   **Gemini API Key** from Google AI Studio

### 1. Environment Setup

Copy your `.env.example` configurations to `.env` in the root folder (or backend folder depending on your path resolving) and fill in your keys:

```env
# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# PostgreSQL Database
DATABASE_URL=postgresql://user:password@localhost:5432/email_db

# Google API settings
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
CALENDAR_TOKEN_PATH=calendar_token.json

# Fetch Configuration
EMAIL_FETCH_LIMIT=5
```

> **Note:** Download your Desktop OAuth `credentials.json` from the Google Cloud Console and place it in the `backend/` directory.

### 2. Backend Setup (FastAPI)

Open a terminal and set up the Python environment:

```bash
cd backend
python -m venv venv

# Activate the virtual environment
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI Server
python -m uvicorn main:app --reload
```
*The backend server will run at `http://localhost:8000` (Swagger UI at `/docs`).*

### 3. Frontend Setup (Next.js)

Open a separate terminal and start the UI:

```bash
cd frontend

# Install Node dependencies
npm install

# Start the development server
npm run dev
```
*The frontend dashboard will run at `http://localhost:3000`.*

---

## 🌐 Core API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/process-emails` | `GET` | Fetches emails from Gmail, passes them through the CrewAI agents and persists insights to PostgreSQL. |
| `/emails` | `GET` | Returns all processed/categorized emails. |
| `/reply-email` | `POST` | Dispatches an email response directly to an existing Gmail thread. |
| `/send-email` | `POST` | Composes and sends a brand new email. |
| `/forward-email`| `POST` | Forwards an existing email with an optional personal memo. |
| `/modify-email` | `POST` | Archives, stars, marks as read, or deletes emails in your inbox. |
| `/create-event` | `POST` | Uses Gemini AI to auto-extract times/locations and create a Google Calendar event. |
| `/generate-reply`| `POST` | Dynamically streams AI-generated 1-3 variation reply drafts. |

---

## 🛠 Tech Stack

*   **Logic Orchestration**: [CrewAI](https://crewai.com) (Multi-Agent System)
*   **Intelligence Engine**: [Google Gemini 2.5 Flash](https://ai.google.dev/)
*   **Web Framework**: [FastAPI](https://fastapi.tiangolo.com)
*   **Frontend**: [Next.js](https://nextjs.org) (React / Tailwind)
*   **Database**: [PostgreSQL](https://www.postgresql.org/) + SQLAlchemy
*   **Integrations**: Google Auth HTTP Libraries (Gmail API, Google Calendar API)

---

## 🔒 Security

*   Store your `credentials.json` and `token.json` securely. They have access to Google Workspace permissions. They are excluded via `.gitignore`.
*   Ensure CORS middleware inside `main.py` is appropriately configured for production environments.
