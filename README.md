# Autonomous Blog Generation Agent

> Production-grade multi-agent blog generation engine powered by LangGraph, FastAPI, Groq, and HuggingFace.

---

## Workflow

```
User Input (topic or transcript)
          │
          ▼
   ┌─────────────┐
   │   Router    │  ── decides needs_web_search + needs_translation
   └─────────────┘
     │           │
   Yes            No
     │             │
     ▼             ▼
┌──────────┐  ┌──────────────┐
│Web Search│  │LLM Knowledge │
│ (Tavily) │  │ (Groq only)  │
└──────────┘  └──────────────┘
     │               │
     └──────┬─────────┘
            ▼
   ┌────────────────┐
   │  Brainstorming │  ── title + 5 section headings
   └────────────────┘
            │
            ▼
   ┌────────────────────┐
   │ Content Generation │  ── full blog draft
   └────────────────────┘
            │
            ▼
   ┌────────────────┐
   │Image Generator │  ── always runs (HuggingFace)
   └────────────────┘
            │
     ┌──────┴──────┐
   Yes              No
     │               │
     ▼               │
┌──────────┐         │
│Translator│         │
└──────────┘         │
     │               │
     └──────┬─────────┘
            ▼
   ┌─────────────┐
   │ SEO Reducer │  ── meta description + keywords
   └─────────────┘
            │
            ▼
   ┌─────────────┐
   │ Save Memory │  ── AsyncSqliteSaver checkpoint
   └─────────────┘
            │
            ▼
   Final Blog Output ✓
```

**State management** flows seamlessly between all nodes via LangGraph's `BlogState` TypedDict. The Router runs once and writes both routing decisions into state — no duplicate LLM calls.

---

## Architecture

### Stage 1: Environment Setup (UV)

Dependency source of truth: [pyproject.toml](pyproject.toml)

Install and sync all dependencies:

```bash
uv sync
```

| File | Purpose |
|---|---|
| `pyproject.toml` | All dependencies defined here |
| `.env` | API keys and environment config |

---

### Stage 2: Multi-Agent DAG (LangGraph)

Graph implementation: [app/graph/workflow.py](app/graph/workflow.py)

Current agent flow:

| Agent | Trigger | Responsibility |
|---|---|---|
| `router` | Always | Decides `needs_web_search` + `needs_translation` |
| `web_search` | `needs_web_search = True` | Fetches real-time evidence via Tavily |
| `llm_knowledge` | `needs_web_search = False` | Uses Groq base knowledge |
| `brainstorming` | Always | Generates blog title + 5 section headings |
| `content_generation` | Always | Writes full blog draft |
| `image_generator` | Always | Generates blog image via HuggingFace |
| `translator` | `needs_translation = True` | Translates blog to target language |
| `seo_reducer` | Always | Trims content, adds meta description + keywords |
| `save_memory` | Always | Persists state via AsyncSqliteSaver |

Conditional routing logic:

```python
# After router node
needs_web_search = True  → web_search    → brainstorming
needs_web_search = False → llm_knowledge → brainstorming

# After image generator
needs_translation = True  → translator  → seo_reducer
needs_translation = False → seo_reducer

# Final path (always)
seo_reducer → save_memory → END
```

---

### Stage 3: Microservice API (FastAPI)

API router: [app/api/blog.py](app/api/blog.py)
App entrypoint: [app/main.py](app/main.py)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/generate_blog` | Primary generation endpoint |
| `POST` | `/api/v1/generate` | Backward-compatible alias |
| `GET` | `/health` | Health check |

Example topic request:

```json
{
  "topic": "The Future of AI in Healthcare",
  "target_language": "english"
}
```

Example transcript request:

```json
{
  "input_type": "transcript",
  "transcript": "Your raw transcript text here...",
  "target_language": "english"
}
```

---

### Stage 4: Observability (LangSmith)

LangSmith is enabled via environment variables and run metadata attached in API calls.

Required `.env` values:

```bash
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
HF_API_KEY=your_huggingface_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=autonomous-blog-agent
```

---

## Project Structure

```
autonomous-blog-generation-agent/
├── app/
│   ├── agents/
│   │   ├── router.py
│   │   ├── research.py
│   │   ├── llm_knowledge.py
│   │   ├── brainstorming.py
│   │   ├── content_generator.py
│   │   ├── image_generator.py
│   │   ├── translator.py
│   │   ├── seo_reducer.py
│   │   └── memory_persist.py
│   ├── api/
│   │   └── blog.py
│   ├── graph/
│   │   └── workflow.py
│   ├── schemas/
│   │   └── blog.py
│   ├── services/
│   │   └── llm_service.py
│   ├── static/
│   │   ├── index.html
│   │   ├── styles.css
│   │   └── app.js
│   └── main.py
├── generated_images/
├── .env
├── pyproject.toml
└── README.md
```

---

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/ANIRUDH1YADAV/autonomous-blog-generation-agent.git
cd autonomous-blog-generation-agent
```

### 2. Configure environment variables

Copy and fill in your `.env` file:

```bash
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
HF_API_KEY=your_huggingface_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=autonomous-blog-agent
```

### 3. Install and run

```bash
uv sync
uv run uvicorn app.main:app --reload
```

---

## Local URLs

| Interface | URL |
|---|---|
| App UI | http://127.0.0.1:8000/ |
| Swagger Docs | http://127.0.0.1:8000/docs |
| Health Check | http://127.0.0.1:8000/health |

---

## Frontend

The UI is served directly by FastAPI — no Streamlit required.

| File | Purpose |
|---|---|
| [app/static/index.html](app/static/index.html) | Main UI structure |
| [app/static/styles.css](app/static/styles.css) | Styling |
| [app/static/app.js](app/static/app.js) | API calls and interactivity |

---

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-latest-purple)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)
![Groq](https://img.shields.io/badge/Groq-LLaMA3-orange)
![LangSmith](https://img.shields.io/badge/LangSmith-Observability-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
